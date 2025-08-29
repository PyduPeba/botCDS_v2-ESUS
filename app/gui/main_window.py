# Arquivo: app/gui/main_window.py
import sys
import os
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout,
                             QPushButton, QTextEdit, QHBoxLayout, QCheckBox,
                             QSizePolicy, QLineEdit, QMessageBox, QComboBox) # Adicionado QComboBox para seleção da tarefa
from PyQt5.QtGui import QPixmap, QPalette, QColor, QBrush, QTextCursor
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QPoint, QTimer, QObject, QMetaObject # Importados QThread, QObject, QMetaObject
import asyncio # Importado asyncio
import pandas as pd # Importado pandas
import csv

# ** IMPORTAÇÃO DE DATETIME **
from datetime import datetime # Importa datetime para manipulação de datas

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

class MainWindow(QWidget): # Renomeado de MinhaApp para MainWindow
    # Sinal que a MainWindow emitirá para o Worker para informar a ação do usuário
    # Este sinal é CONECTADO a um slot NO WORKER
    user_action_signal = pyqtSignal(str) # Emite 'continue', 'skip', ou 'abort'

    def __init__(self):
        super().__init__()

        # Instâncias para gerenciar a thread de automação e o worker
        self._automation_thread = None
        self._automation_worker: Worker = None

        self.main_layout = None # Definir layout principal
        self._file_manager = FileManager() # Instância do gerenciador de arquivos

        self.initUI()
        self._load_initial_date() # Carrega a data inicial ao abrir a janela

    def set_background_image(self, image_path_relative):
        """Configura a imagem de fundo usando um caminho relativo à pasta resources/img."""
        # Determina o caminho completo para a imagem na pasta "resources/img"
        # BASE_DIR está definido no AppConfig
        img_path = AppConfig.BASE_DIR / "resources" / "img" / image_path_relative

        if not img_path.exists():
             logger.warning(f"Imagem de fundo não encontrada: {img_path}")
             # Tenta o caminho relativo original se o novo não funcionar (compatibilidade ou debug)
             img_path = Path(os.path.dirname(os.path.abspath(__file__))) / ".." / "img" / image_path_relative
             if not img_path.exists():
                 logger.warning(f"Imagem de fundo não encontrada no caminho de fallback: {img_path}")
                 return # Não faz nada se a imagem não for encontrada

        logger.info(f"Carregando imagem de fundo: {img_path}")
        try:
             # Crie um QLabel para exibir a imagem
             background_label = QLabel(self)
             pixmap = QPixmap(str(img_path)) # Use str() para compatibilidade com QPixmap

             if pixmap.isNull():
                  logger.warning(f"Não foi possível carregar a imagem de fundo de {img_path}")
                  return

             # Redimensionar pixmap para a largura da janela (ajuste conforme necessário)
             # Nota: Redimensionar aqui pode distorcer a imagem. É melhor deixar o layout/auto size lidar com isso
             # ou usar um QLabel com scaledContents=True dentro de um layout.
             # Para um fundo fixo, setting geometry manualmente ou usando um QPalette com backgroundBrush é comum.
             # Vamos manter o método original por enquanto, mas esteja ciente das limitações.
             # Uma abordagem mais robusta para fundo seria usar QPalette.
             # Exemplo básico com QPalette:
             # palette = QPalette()
             # palette.setBrush(QPalette.Background, QBrush(pixmap.scaled(self.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)))
             # self.setPalette(palette)
             # self.setAutoFillBackground(True)

             # Abordagem original (menos robusta para redimensionamento da janela)
             pixmap = pixmap.scaledToWidth(self.width()) # Redimensiona para a largura atual da janela
             background_label.setPixmap(pixmap)

             # Configurar o QLabel para centralizá-lo na janela (ajustar lógica de posicionamento)
             # Posicionar elementos fixos sobre um fundo redimensionável é tricky com layout manual.
             # Vamos confiar nos layouts para a maioria dos elementos e talvez usar um QLabel para a imagem com size policy.
             # Por enquanto, apenas exibe a imagem, o posicionamento pode precisar de ajuste fino.
             # background_label.setGeometry(0, 0, pixmap.width(), pixmap.height()) # Posiciona no canto superior esquerdo
             # background_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
             # background_label.setScaledContents(True) # Permite que o QLabel escale o pixmap

             # Para o seu layout atual, posicionar manualmente PODE funcionar, mas é frágil.
             # label_width = pixmap.width()
             # label_height = pixmap.height()
             # label_x = (self.width() - label_width) // 2
             # label_y = (self.height() - label_height) // 2
             # background_label.setGeometry(label_x, label_y, label_width, label_height)
             pass # Vamos remover o posicionamento manual e focar nos layouts para os outros elementos
        except Exception as e:
             logger.error(f"Erro ao configurar imagem de fundo: {e}")


    def initUI(self):
        """Configura a interface gráfica principal."""
        # Configurar a imagem de fundo (chame ANTES de configurar o layout principal se for manual)
        # Para uma abordagem mais PyQt-like, considere usar QPalette no futuro.
        # self.set_background_image("capa.png") # Desativado o posicionamento manual na função


        # Layout principal
        self.main_layout = QVBoxLayout(self) # Define o layout principal para a janela

        # Configuração de margens e alinhamentos para o layout principal
        # Ajuste as margens e espaçamento conforme necessário
        # self.main_layout.setContentsMargins(50, 205, 150, 150) # Margens manuais podem conflitar com layouts
        self.main_layout.setSpacing(10) # Espaçamento entre widgets

        # --- Elementos da GUI ---

        # QLabel para a instrução inicial
        # label = MovableLabel('Escolha uma opção:', self) # Usar MovableLabel é desnecessário com layouts
        label = QLabel('Escolha uma opção:', self)
        label.setStyleSheet("font-size: 15pt;")
        # Alinhe o label à esquerda ou centro conforme desejado
        # label.setAlignment(Qt.AlignLeft)
        self.main_layout.addWidget(label)

        # ComboBox para selecionar o tipo de tarefa
        task_label = QLabel('Selecionar Tarefa:', self)
        task_label.setStyleSheet("font-size: 12pt;")
        self.main_layout.addWidget(task_label)

        self.task_combobox = QComboBox(self)
        # Adiciona os nomes das tarefas do nosso mapa TASK_MAP
        self.task_combobox.addItems(TASK_MAP.keys())
        self.task_combobox.setStyleSheet("font-size: 12pt;")
        self.main_layout.addWidget(self.task_combobox)


        # --- Entrada de Data ---
        # Usaremos um QHBoxLayout para colocar o label, campo de texto e botão Salvar Data lado a lado
        date_layout = QHBoxLayout()

        self.data_label = QLabel("Inserir a Data:", self)
        self.data_label.setStyleSheet("font-size: 12pt;")
        date_layout.addWidget(self.data_label) # Adiciona ao layout horizontal

        self.data_edit = QLineEdit(self)
        self.data_edit.setPlaceholderText("dd/mm/aaaa") # Texto de placeholder
        self.data_edit.setInputMask("99/99/9999") # Máscara para garantir formato
        self.data_edit.setStyleSheet("font-size: 12pt;")
        self.data_edit.editingFinished.connect(self.format_date) # Formata ao sair do campo
        date_layout.addWidget(self.data_edit) # Adiciona ao layout horizontal

        self.save_date_button = QPushButton('Salvar Data', self)
        self.set_button_style(self.save_date_button, "red") # Estilo inicial vermelho
        self.save_date_button.clicked.connect(self.save_date_to_csv)
        date_layout.addWidget(self.save_date_button) # Adiciona ao layout horizontal

        # Adiciona o layout horizontal de data ao layout principal
        self.main_layout.addLayout(date_layout)

        # --- CHECKBOX DE LOGIN MANUAL (NOVO) ---
        self.checkbox_manual_login = QCheckBox("Login Manual para outros perfis (ACS/Médico)", self) # <-- NOVO
        self.checkbox_manual_login.setStyleSheet("font-size: 10pt; font-style: italic; color: #333;") # <-- NOVO
        self.checkbox_manual_login.setToolTip("Marque esta opção se precisar selecionar manualmente o perfil/equipe após o login (ex: ACS, Médico). O robô fará uma pausa de 5 segundos.") # <-- NOVO
        self.main_layout.addWidget(self.checkbox_manual_login) # <-- NOVO
        # --- FIM DO NOVO BLOCO ---

        # --- CheckBox para apagar arquivo ---
        self.checkboxDeleteFile = QCheckBox("Apagar dados.csv após conclusão?", self)
        self.checkboxDeleteFile.setStyleSheet("font-size: 10pt;")
        # Conecta o sinal stateChanged para salvar a configuração imediatamente
        self.checkboxDeleteFile.stateChanged.connect(self.on_checkbox_delete_changed)
        # Carrega o estado salvo ao iniciar
        self.checkboxDeleteFile.setChecked(AppConfig.delete_file_after_completion)
        self.main_layout.addWidget(self.checkboxDeleteFile)

        # --- Botões de Automação ---
        # Usaremos um layout vertical ou horizontal para organizar os botões
        # Vamos criar um layout para os botões principais de iniciar
        button_start_layout = QVBoxLayout() # Layout vertical para os botões de iniciar

        # Removendo os botões individuais por tipo e substituindo por um botão "Iniciar Automação" genérico
        # self.btn_atendimento_hipertenso = QPushButton('Atendimento Hipertenso', self) # REMOVIDO
        # self.btn_procedimentos_afericao = QPushButton('Procedimentos Aferição', self) # REMOVIDO
        # ... outros botões removidos ...

        self.btn_start_automation = QPushButton('Iniciar Automação', self)
        self.btn_start_automation.setFixedSize(250, 60) # Tamanho fixo maior
        self.btn_start_automation.setStyleSheet("font-size: 16pt;")
        self.btn_start_automation.clicked.connect(self.start_automation) # Conecta ao novo método de iniciar
        button_start_layout.addWidget(self.btn_start_automation, alignment=Qt.AlignCenter) # Centraliza o botão

        # Adiciona o layout dos botões de iniciar ao layout principal
        self.main_layout.addLayout(button_start_layout)

        # --- Área para Log/Status (Opcional mas útil) ---
        # Podemos adicionar uma área de texto para mostrar o log ou status em tempo real
        # log_label = QLabel("Log/Status:")
        # self.main_layout.addWidget(log_label)
        # self.log_text_edit = QTextEdit(self)
        # self.log_text_edit.setReadOnly(True)
        # self.main_layout.addWidget(self.log_text_edit)
        # Nota: Integrar o logger.py para escrever aqui requer um handler customizado para PyQt.

        # --- Botão Exit ---
        self.btn_exit = QPushButton('Exit', self)
        self.btn_exit.setFixedSize(100, 40) # Tamanho menor
        self.btn_exit.clicked.connect(self.exit_app)
        # Adicionar o botão de saída em um layout separado para posicionamento específico
        exit_layout = QHBoxLayout()
        exit_layout.addStretch(1) # Empurra o botão para a direita
        exit_layout.addWidget(self.btn_exit)
        self.main_layout.addLayout(exit_layout)

        # --- Créditos e Versão ---
        # Estes podem ser adicionados em um layout horizontal na parte inferior
        info_layout = QHBoxLayout()

        self.creditos_label = QLabel("Copyright DIGT and Kʎɐꓘ", self)
        self.creditos_label.setWordWrap(True) # Permite quebra de linha
        info_layout.addWidget(self.creditos_label)

        self.version_pec_label = QLabel('PEC: Versão 5.3.19', self) # Renomeado para clareza
        self.version_pec_label.setStyleSheet("color: green; font-weight: bold; font-size: 12px;")
        info_layout.addWidget(self.version_pec_label)

        self.version_app_label = QLabel('App Version: 2.0', self) # Versão do seu app
        self.version_app_label.setStyleSheet("color: blue; font-weight: bold; font-size: 12px;")
        info_layout.addWidget(self.version_app_label)

        self.main_layout.addLayout(info_layout)


        # Configurações da janela principal
        self.setGeometry(100, 100, 700, 600)  # Tamanho inicial
        self.setWindowTitle('Robo DIGT v2.0 (Playwright/Asyncio)') # Novo título

        # Define o layout principal para a janela
        self.setLayout(self.main_layout)

        # Habilitar/desabilitar botões durante a automação (inicialmente habilitados)
        self._set_ui_enabled(True)

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
        AppConfig.set_delete_file_after_completion(state == Qt.Checked)
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

        # Se tudo estiver OK, iniciar a thread
        logger.info(f"Iniciando automação para a tarefa '{selected_task_name}'...")
        self._set_ui_enabled(False) # Desabilita a UI durante a automação

        # Cria a thread de trabalho
        self._automation_thread = QThread()
        # Cria o objeto Worker e o move para a thread
        self._automation_worker = Worker(selected_task_name, manual_login=is_manual_login)
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
        QApplication.quit() # Fecha a aplicação PyQt