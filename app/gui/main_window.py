#app/gui/main_window.py (VERSÃO v3a - Ajuste de Layout Data)
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QLineEdit, QPushButton, QCheckBox, QFrame, QGridLayout, QMessageBox
)
from PyQt5.QtCore import Qt, QDate, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPalette

import csv
import sys
import os

# Suporte a lógica de automação
from datetime import datetime

# Importa componentes do nosso app
from app.core.app_config import AppConfig
from app.core.logger import logger # Usaremos o logger configurado
from app.core.errors import AutomationError # Para type hinting no signal
from app.automation.error_handler import SkipRecordException, AbortAutomationException # Para type hinting
from app.gui.worker import Worker, TASK_MAP # Importa o Worker e o mapa de tarefas
from app.gui.dialogs import ErrorDialog # Importa o diálogo de erro
from app.data.file_manager import FileManager # Para lidar com o arquivo de data

class MovableLabel(QLabel):
    # Mantido da versão original, pode ser removido se não for mais usado para posicionamento complexo
    def __init__(self, text, parent=None):
        super().__init__(text, parent)

    def move_up(self, pixels):
        self.setGeometry(self.x(), self.y() - pixels, self.width(), self.height())


class MainWindow(QWidget):

    user_action_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._automation_thread = None
        self._automation_worker: Worker = None
        self._use_chrome_browser = False

        self.main_layout = None
        self._file_manager = FileManager()
        self.initUI()
        self._load_initial_date()

    def initUI(self):
        """Configura a interface gráfica principal."""
        # Configurar a imagem de fundo (chame ANTES de configurar o layout principal se for manual)
        # Para uma abordagem mais PyQt-like, considere usar QPalette no futuro.
        # self.set_background_image("capa.png") # Desativado o posicionamento manual na função
        # --- NOVA LÓGICA PARA TÍTULO DINÂMICO ---
        # 1. Obtém o caminho do executável ou script
        if getattr(sys, 'frozen', False):
            # Se for um executável PyInstaller
            app_path = os.path.dirname(sys.executable)
        else:
            # Se for um script Python (ambiente de desenvolvimento)
            app_path = os.path.dirname(os.path.abspath(__file__))

        # 2. Extrai os nomes das últimas duas pastas
        # Ex: C:\Users\CeearaU\Desktop\BotTratamento\pasta_de_saida\ipu_hipertensao\INGAZEIRA
        # last_folder_name = INGAZEIRA
        # second_last_folder_name = ipu_hipertensao
        last_folder_name = os.path.basename(app_path)
        second_last_folder_name = os.path.basename(os.path.dirname(app_path))

        # 3. Concatena os nomes para o título da janela
        extra_title_info = ""
        if second_last_folder_name and second_last_folder_name != "dist" and second_last_folder_name != "site-packages":
            extra_title_info += f" - {second_last_folder_name}"
        if last_folder_name and last_folder_name != "dist" and last_folder_name != "site-packages":
            extra_title_info += f" - {last_folder_name}"
        
        # Garante que não adicionamos "dist" ou "site-packages" se estiver em caminhos temporários
        if "dist" in app_path or "site-packages" in app_path:
             extra_title_info = "" # Limpa se for um caminho de compilação ou venv

        self.setWindowTitle(f'CDS ESUS v5.3.3c{extra_title_info}')
        self.setGeometry(100, 100, 400, 350) #antes 500 x 350
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(240, 242, 245))
        self.setPalette(palette)

        main_layout = QVBoxLayout() # Layout principal vertical
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(10)

        title_label = QLabel('CDS DIGT <span style="font-weight:bold; color:#4C72E0;">v5.3.3c</span>')
        title_label.setFont(QFont('Segoe UI', 28, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setTextFormat(Qt.RichText)
        main_layout.addWidget(title_label)

        subtitle_label = QLabel('Automação inteligente e eficiente com Playwright/Asyncio')
        subtitle_label.setFont(QFont('Segoe UI', 11))
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("color: #6B7280;")
        main_layout.addWidget(subtitle_label)

        content_grid = QGridLayout()
        content_grid.setHorizontalSpacing(15) # Espaçamento horizontal entre colunas
        content_grid.setVerticalSpacing(15) # Espaçamento vertical entre linhas
        content_grid.setAlignment(Qt.AlignCenter)

        # --- CARD TAREFA ---
        task_card = QFrame()
        task_card.setFixedWidth(250)
        task_card.setMinimumWidth(250)
        task_card.setMinimumHeight(240)
        task_card.setMaximumHeight(300)
        task_card.setStyleSheet("""
            QFrame {
                background-color: white;
                border-top-left-radius: 0px;
                border-bottom-left-radius: 0px;
                border-top-right-radius: 20px;
                border-bottom-right-radius: 20px;
                padding: 15px;
            }
        """)
        task_layout = QVBoxLayout(task_card)
        task_layout.setSpacing(1)
        task_layout.addWidget(QLabel('<span style="font-size:18px; font-weight:bold;">Definir Tarefa</span>'), alignment=Qt.AlignCenter)
        task_label = QLabel('Escolhe a tarefa:')
        task_label.setFont(QFont('Segoe UI', 11))
        # task_label.setStyleSheet("margin-top: -8px;")
        task_layout.addWidget(task_label)
        self.task_combobox = QComboBox()
        self.task_combobox.addItems(TASK_MAP.keys())
        self.task_combobox.setFont(QFont('Segoe UI', 11))
        self.task_combobox.setStyleSheet("""
            QComboBox {
                padding: 12px;
                border: 1px solid #4C72E0;
                border-radius: 15px;
                background-color: #F8F9FA;
            }
            QComboBox::drop-down {
                border: none;
                padding-right: 15px;
            }
            QComboBox::down-arrow {
                image: url(data:image/svg+xml;utf8,<svg width='14' height='14' viewBox='0 0 24 24' fill='none' stroke='%234C72E0' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><rect x='2' y='2' width='20' height='20' rx='3' ry='3' fill='%23F8F9FA' stroke='%234C72E0' stroke-width='1'/><polyline points='6 9 12 15 18 9'/></svg>);
                width: 14px;
                height: 14px;
                margin-right: 8px;
            }
            QComboBox::view {
                border: 1px solid #4C72E0;
                border-radius: 5px;
                background-color: white;
                selection-background-color: #4C72E0;
                selection-color: white;
                outline: 0px;
                padding: 5px;
            }
            QComboBox::view::item {
                padding: 10px 8px;
                min-height: 25px;
            }
            QComboBox::view::item:hover {
                background-color: #E0E9FF;
                color: #333;
            }
        """)
        task_layout.addWidget(self.task_combobox)
        task_layout.addStretch(1)
        content_grid.addWidget(task_card, 0, 0)

        # --- CARD DATA ---
        date_card = QFrame()
        date_card.setFixedWidth(250)
        date_card.setMinimumWidth(250)
        date_card.setMinimumHeight(240)
        date_card.setMaximumHeight(300)
        date_card.setStyleSheet("""
            QFrame {
                background-color: white;
                border-top-left-radius: 20px;
                border-bottom-left-radius: 20px;
                border-top-right-radius: 0px;
                border-bottom-right-radius: 0px;
                padding: 15px;
            }
        """)
        date_layout = QVBoxLayout(date_card)
        date_layout.setSpacing(1)
        date_layout.addWidget(QLabel('<span style="font-size:18px; font-weight:bold;">Config Data</span>'), alignment=Qt.AlignCenter)
        date_label = QLabel('Insira a data inicial:')
        date_label.setFont(QFont('Segoe UI', 11))
        date_layout.addWidget(date_label)
        row_date_layout = QHBoxLayout()
        row_date_layout.setSpacing(5)
        self.data_edit = QLineEdit()
        self.data_edit.setInputMask("99/99/9999")
        self.data_edit.setFont(QFont('Segoe UI', 11))
        self.data_edit.editingFinished.connect(self.format_date)
        self.data_edit.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                border: 1px solid #ccc;
                border-radius: 15px;
                background-color: #F8F9FA;
            }
        """)
        row_date_layout.addWidget(self.data_edit)
        self.save_date_button = QPushButton("Save Data")
        self.save_date_button.setFont(QFont('Segoe UI', 11, QFont.Bold))
        self.save_date_button.setStyleSheet("""
            QPushButton {
                background-color: #28A745;
                color: white;
                padding: 12px 15px;
                border-radius: 15px;
            }
        """)
        self.save_date_button.clicked.connect(self.save_date_to_csv)
        row_date_layout.addWidget(self.save_date_button)
        date_layout.addLayout(row_date_layout)
        date_layout.addStretch(1)
        content_grid.addWidget(date_card, 0, 1)

        # --- CARD AÇÕES ---
        action_card = QFrame()
        action_card.setStyleSheet("QFrame { background-color: white; border-radius: 10px; padding: 10px; }")
        action_layout = QVBoxLayout(action_card)
        action_layout.setSpacing(5)

        self.checkbox_manual_login = QCheckBox("Login Manual (ACS/Médico)")
        self.checkbox_manual_login.setFont(QFont('Segoe UI', 11))
        self.checkboxDeleteFile = QCheckBox("Apagar “dados.csv” após concluir")
        self.checkboxDeleteFile.stateChanged.connect(self.on_checkbox_delete_changed)
        self.checkboxDeleteFile.setFont(QFont('Segoe UI', 11))

        # --- Alternar entre Firefox/Chrome ---
        self.checkbox_use_chrome = QCheckBox("Usar Navegador Chrome")
        self.checkbox_use_chrome.setFont(QFont('Segoe UI', 11))
        self.checkbox_use_chrome.stateChanged.connect(self.on_checkbox_use_chrome_changed)
        action_layout.addWidget(self.checkbox_use_chrome) # Adiciona ao layout do CARD AÇÕES


        action_layout.addWidget(self.checkbox_manual_login)
        action_layout.addWidget(self.checkboxDeleteFile)

        self.btn_start_automation = QPushButton("Iniciar Automação")
        self.btn_start_automation.setFont(QFont('Segoe UI', 14, QFont.Bold))
        self.btn_start_automation.setFixedSize(200, 60)
        self.btn_start_automation.clicked.connect(self.start_automation) # Conecta ao novo método de iniciar
        self.btn_start_automation.setStyleSheet("""
            QPushButton {
                background-color: #4461D7;
                color: white;
                border-radius: 20px;
            }
        """)
        action_layout.addWidget(self.btn_start_automation, alignment=Qt.AlignCenter)

        # --- Botão Sair ---
        self.btn_exit = QPushButton("Sair")
        self.btn_exit.setFixedSize(100, 35)
        self.btn_exit.setFont(QFont('Segoe UI', 11, QFont.DemiBold))
        self.btn_exit.clicked.connect(self.exit_app)
        action_layout.addWidget(self.btn_exit, alignment=Qt.AlignCenter)

        content_grid.addWidget(action_card, 1, 0, 1, 2)
        main_layout.addLayout(content_grid)

        # Rodapé
        footer = QHBoxLayout()
        copyright = QLabel("© 2025 Kʎɐꓘ")
        copyright.setFont(QFont('Segoe UI', 10))
        version_pec = QLabel('PEC: <span style="color:green;">Versão 5.4.11</span>')
        version_pec.setTextFormat(Qt.RichText)
        version_app = QLabel('App Version: <span style="color:#4461D7;">5.3.2</span>')
        version_app.setTextFormat(Qt.RichText)
        footer.addWidget(copyright)
        footer.addStretch()
        footer.addWidget(version_pec)
        footer.addWidget(version_app)
        main_layout.addLayout(footer)

        self.setLayout(main_layout)

        self._set_ui_enabled(True) # Garante que a UI comece habilitada

    def on_checkbox_use_chrome_changed(self, state):
        """Slot para salvar a configuração do checkbox 'Usar Navegador Chrome'."""
        self._use_chrome_browser = (state == Qt.Checked)
        logger.info(f"Config 'Usar Navegador Chrome': {self._use_chrome_browser}")

    def _load_initial_date(self):
        """Carrega a data salva em data.csv ao iniciar o app."""
        date_str = self._file_manager.load_main_date_file()
        if date_str:
            self.data_edit.setText(date_str)
            # Mudar a cor do botão para verde se uma data foi carregada (assumindo que foi salva antes)
            self.set_button_style(self.save_date_button, "green")
        else:
             self.data_edit.clear()
             self.set_button_style(self.save_date_button, "red")

    def format_date(self):
        """Formata o texto inserido para o formato dd/mm/aaaa e valida."""
        text = self.data_edit.text()
        formatted_text = ''.join(filter(str.isdigit, text))

        # Adicionando as barras no lugar correto
        if len(formatted_text) >= 8:
            formatted_text = formatted_text[:2] + '/' + formatted_text[2:4] + '/' + formatted_text[4:8]
        elif len(formatted_text) >= 4:
            formatted_text = formatted_text[:2] + '/' + formatted_text[2:4]
        elif len(formatted_text) >= 2:
            formatted_text = formatted_text[:2]

        self.data_edit.setText(formatted_text)

        # Valida o formato completo (dd/mm/aaaa)
        if len(formatted_text) == 10:
             try:
                 datetime.strptime(formatted_text, "%d/%m/%Y")
                 # Data parece válida
                 self.set_button_style(self.save_date_button, "green") # Muda para verde se formato OK
                 logger.debug(f"Formato de data validado: {formatted_text}")
             except ValueError:
                 QMessageBox.warning(self, "Data Inválida", "Por favor, insira uma data válida no formato dd/mm/aaaa.")
                 self.set_button_style(self.save_date_button, "red") # Volta para vermelho se inválida
        else:
             # Se o formato não tem 10 caracteres, ainda não é uma data completa no formato esperado
             self.set_button_style(self.save_date_button, "red")
    
    def set_button_style(self, button, color):
        """Define o estilo (cor) de um botão."""
        if color == "red":
            button.setStyleSheet("""
                QPushButton {
                    background-color: #FF5733;
                    color: white;
                    border-radius: 10px;
                    padding: 5px;
                    font-size: 14px;
                }
                QPushButton:disabled {
                    background-color: #FFA07A; /* Cor mais clara quando desabilitado */
                    color: #D3D3D3;
                }
            """)
        elif color == "green":
            button.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border-radius: 10px;
                    padding: 5px;
                    font-size: 14px;
                }
                 QPushButton:disabled {
                    background-color: #90EE90; /* Cor mais clara quando desabilitado */
                    color: #D3D3D3;
                }
            """)
        else: # Estilo padrão ou outro
             button.setStyleSheet("") # Reseta para o estilo padrão

    def save_date_to_csv(self):
        """
        Salva a data formatada em um arquivo CSV. Substitui qualquer dado existente.
        """
        date_text = self.data_edit.text()
        if len(date_text) != 10:
             QMessageBox.warning(self, "Data Incompleta", "Por favor, insira a data completa no formato dd/mm/aaaa antes de salvar.")
             self.set_button_style(self.save_date_button, "red") # Garante que o botão fique vermelho se a data não estiver completa
             return

        try:
            # Valida se a data é um formato válido de data real
            datetime.strptime(date_text, "%d/%m/%Y")

            # O FileManager já sabe onde salvar (resources/data_input/data.csv)
            data_file_path = self._file_manager.DATA_DIR / "data.csv"

            # Reescreve o arquivo com a nova data
            with open(data_file_path, mode='w', newline='', encoding='utf-8') as file: # Use utf-8 e newline=''
                writer = csv.writer(file)
                writer.writerow(['DATA'])  # Cabeçalho
                writer.writerow([date_text])    # Nova data

            # Chamar a função de log (esta função deveria estar no módulo de data ou core)
            # Vamos adicionar um método para logar data usada no FileManager ou DateSequencer
            # Por enquanto, apenas printa/loga com o logger
            logger.info(f"Data '{date_text}' salva em {data_file_path}")
            # A função original write_log também escrevia em log_de_data_usadas.txt na raiz.
            # Podemos replicar isso ou confiar apenas no logger.
            self._log_used_date_to_file(date_text) # Chama o log adicional

            self.set_button_style(self.save_date_button, "green")
            QMessageBox.information(self, "Data Salva", f"Data {date_text} salva com sucesso.")

        except ValueError:
             QMessageBox.warning(self, "Data Inválida", "Por favor, insira uma data real válida no formato dd/mm/aaaa.")
             self.set_button_style(self.save_date_button, "red")
        except Exception as e:
            logger.error(f"Erro ao salvar os dados: {e}", exc_info=True)
            QMessageBox.critical(self, "Erro ao Salvar", f"Ocorreu um erro ao salvar a data: {e}")
            self.set_button_style(self.save_date_button, "red")
            
    def _log_used_date_to_file(self, user_date):
         """Escreve a data usada em um arquivo de log separado, replicando o comportamento original."""
         # Determina o caminho do arquivo de log na raiz do projeto
         log_file_path = AppConfig.BASE_DIR / 'log_de_data_usadas.txt'
         current_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

         try:
             with open(log_file_path, "a", encoding='utf-8') as log_file:
                 log_file.write(f"Data inserida/usada: {user_date}, Data e Hora de Uso: {current_time}\n")
             logger.debug(f"Data usada logada em {log_file_path}")
         except Exception as e:
             logger.error(f"Erro ao escrever log de data usada em {log_file_path}: {e}")

    def on_checkbox_delete_changed(self, state):
        """Slot para salvar a configuração do checkbox."""
        AppConfig.delete_file_after_completion = (state == Qt.Checked)
        logger.info(f"Config 'Apagar dados.csv': {AppConfig.delete_file_after_completion}")

    def start_automation(self):
        """Inicia a automação em uma nova thread."""
        logger.info("Botão 'Iniciar Automação' clicado.")

        # Validar se a data principal foi salva (botão verde)
        if self.save_date_button.styleSheet().find("background-color: #4CAF50") == -1:
             QMessageBox.warning(self, "Data Não Salva", "Por favor, salve a data principal antes de iniciar a automação.")
             return

        # Obter o tipo de tarefa selecionado
        selected_task_name = self.task_combobox.currentText()
        if not selected_task_name:
            QMessageBox.warning(self, "Tarefa Não Selecionada", "Por favor, selecione um tipo de tarefa.")
            return

        # Obter o primeiro arquivo de dados a processar
        first_data_file = self._file_manager.find_next_file_to_process()
        if not first_data_file:
            QMessageBox.information(self, "Sem Arquivos", "Nenhum arquivo de dados para processar encontrado na pasta resources/data_input/arquivos/.")
            logger.info("Nenhum arquivo para processar encontrado.")
            return

        # Validar se o arquivo principal dados.csv existe (na pasta data_input)
        main_data_csv = self._file_manager.DATA_DIR / "dados.csv"
        if not main_data_csv.exists():
             QMessageBox.warning(self, "Arquivo Principal Faltando", f"Arquivo principal de dados não encontrado: {main_data_csv}.\nPor favor, coloque o primeiro arquivo a ser processado com o nome 'dados.csv' diretamente na pasta '{self._file_manager.DATA_DIR}' e os demais arquivos na subpasta 'arquivos/'.")
             logger.error(f"Arquivo principal dados.csv não encontrado: {main_data_csv}")
             return

        # Validar se o arquivo de configuração de login existe e tem dados
        from app.data.config_loader import ConfigLoader
        config_loader = ConfigLoader()
        login_config = config_loader.load_config()
        if not login_config or not login_config.get("url") or not login_config.get("usuario") or not login_config.get("senha"):
             QMessageBox.warning(self, "Configuração Faltando", f"Arquivo de configuração '{config_loader.CONFIG_FILE}' incompleto ou faltando (URL, Usuário, Senha).")
             logger.error(f"Arquivo de configuração de login incompleto ou faltando: {config_loader.CONFIG_FILE}")
             return

        # --- OBTÉM O ESTADO DO CHECKBOX DE LOGIN MANUAL (MODIFICADO) ---
        is_manual_login = self.checkbox_manual_login.isChecked() # <-- NOVO
        logger.info(f"Modo de Login Manual: {'Ativado' if is_manual_login else 'Desativado'}") # <-- NOVO

        # --- NOVO: OBTÉM O ESTADO DO CHECKBOX DO NAVEGADOR ---
        use_chrome = self.checkbox_use_chrome.isChecked() # Pega o estado atual
        logger.info(f"Usar Navegador Chrome: {'Sim' if use_chrome else 'Não (Firefox)'}")

        # Se tudo estiver OK, iniciar a thread
        logger.info(f"Iniciando automação para a tarefa '{selected_task_name}'...")
        self._set_ui_enabled(False) # Desabilita a UI durante a automação

        # Cria a thread de trabalho
        self._automation_thread = QThread()
        # Cria o objeto Worker e o move para a thread
        # self._automation_worker = Worker(selected_task_name, manual_login=is_manual_login)
        self._automation_worker = Worker(selected_task_name, manual_login=is_manual_login, use_chrome_browser=use_chrome)
        self._automation_worker.moveToThread(self._automation_thread)

        # Conecta sinais do Worker aos slots na MainWindow
        # Quando a thread inicia, chama o método run_automation do worker
        self._automation_thread.started.connect(self._automation_worker.run_automation)
        # Quando o worker termina (sucesso ou falha), para a thread
        self._automation_worker.finished.connect(self._automation_thread.quit)
        # Conecta o sinal finished da thread para limpar o worker e a thread depois
        self._automation_thread.finished.connect(self._automation_worker.deleteLater)
        self._automation_worker.finished.connect(self._automation_worker.deleteLater) # Conecta deleteLater ao sinal do worker

        # Conecta o sinal do Worker para solicitar o diálogo de erro
        # Este sinal é emitido pelo worker e recebido na THREAD PRINCIPAL (MainWindow)
        self._automation_worker.request_error_dialog.connect(self.handle_error_dialog_request)

        # Conecta o sinal finished do Worker a um método na MainWindow para lidar com o resultado
        self._automation_worker.finished.connect(self.on_automation_finished)

        self.user_action_signal.connect(self._automation_worker._handle_user_action_signal)
        # Inicia a thread
        self._automation_thread.start()
        logger.info("Thread de automação iniciada.")

    def _set_ui_enabled(self, enabled: bool):
        """Habilita ou desabilita os controles da UI principal."""
        self.task_combobox.setEnabled(enabled)
        self.data_edit.setEnabled(enabled)
        self.save_date_button.setEnabled(enabled)
        self.checkboxDeleteFile.setEnabled(enabled)
        self.btn_start_automation.setEnabled(enabled)
        # self.btn_exit.setEnabled(enabled) # Pode querer deixar o botão Exit sempre habilitado
        # Se houver outros botões de iniciar tarefa, desabilitar todos eles
        # Se houver uma área de log, talvez habilitar (log_text_edit.setEnabled(True))

    def handle_error_dialog_request(self, error_obj: object):
        """
        Slot chamado pelo Worker (na thread principal) para exibir o diálogo de erro.
        Recebe a instância da AutomationError.
        """
        logger.warning("MainWindow: Recebido request_error_dialog signal. Exibindo diálogo...")
        # O objeto recebido pelo sinal é a instância da AutomationError
        error: AutomationError = error_obj

        # Exibe o diálogo modal. exec_() bloqueia A THREAD PRINCIPAL.
        dialog = ErrorDialog(error, self) # Passa 'self' como parent
        result_code = dialog.exec_() # Bloqueia aqui

        # Quando o diálogo é fechado, obtém a ação escolhida pelo usuário
        user_action = dialog.get_result()
        logger.info(f"MainWindow: Diálogo de erro fechado. Ação escolhida: {user_action}")

        # Envia a ação escolhida de volta para o Worker usando o sinal
        # Este sinal será recebido pelo slot user_action_received no Worker
        # que rodará na thread do Worker.
        if self._automation_worker: # Garante que o worker ainda existe
             self.user_action_signal.emit(user_action) # Emite o sinal com a ação
             logger.debug(f"MainWindow: Sinal user_action_signal emitido com '{user_action}'.")
        else:
             logger.error("MainWindow: Worker não existe ao tentar enviar ação do usuário!")
             # Se o worker não existe, a automação já deve ter terminado ou abortado de outra forma.

    def on_automation_finished(self, result_message: str):
        """Slot chamado quando o Worker termina (sinal finished)."""
        logger.info(f"MainWindow: Automação finalizada com resultado: {result_message}")

        # Habilita a UI principal novamente
        self._set_ui_enabled(True)

        # Exibe uma mensagem para o usuário
        if result_message == "Sucesso":
            QMessageBox.information(self, "Automação Concluída", "A automação foi concluída com sucesso!")
        elif "Falha" in result_message or "Erro fatal" in result_message:
             QMessageBox.critical(self, "Automação Falhou", f"A automação falhou:\n{result_message}")
        elif "Terminada" in result_message:
             QMessageBox.warning(self, "Automação Interrompida", f"A automação foi interrompida:\n{result_message}")
        else:
             QMessageBox.information(self, "Automação Finalizada", f"A automação finalizou:\n{result_message}")

        # Limpar referências ao worker e thread (deleteLater já conectado)
        self._automation_worker = None
        self._automation_thread = None
        logger.info("Referências do Worker e Thread limpas.")

    def exit_app(self):
        """Fecha o aplicativo. Tenta garantir que a thread de automação pare primeiro."""
        logger.info("Botão 'Exit' clicado. Encerrando aplicativo.")
        if self._automation_thread and self._automation_thread.isRunning():
             logger.warning("Thread de automação ainda rodando. Tentando encerrar...")
             # Emite um sinal de abortar para o worker se possível
             if self._automation_worker:
                  # Se o Worker estiver esperando por ação do usuário no diálogo,
                  # emitir 'abort' vai quebrar a espera e o loop principal.
                  self.user_action_signal.emit("abort") # Sinaliza para abortar

             # Espera um pouco para a thread encerrar
             if not self._automation_thread.wait(2000): # Espera até 2 segundos
                  logger.error("Thread de automação não encerrou graciosamente. Terminando aplicativo à força.")
                  # Força o encerramento da thread (não recomendado, pode deixar recursos abertos)
                  # self._automation_thread.terminate() # Descomente se precisar forçar muito
                  # self._automation_thread.wait() # Espera terminar após o terminate
        QApplication.quit()

# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     win = MainWindow()
#     win.show()
#     sys.exit(app.exec_())
