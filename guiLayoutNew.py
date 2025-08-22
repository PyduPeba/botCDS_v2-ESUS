import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QLineEdit, QPushButton, QCheckBox, QMessageBox, QFrame, QGridLayout, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont, QColor, QPalette

class RoboDIGTAppV5(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Configurações da janela principal
        self.setWindowTitle('Robo DIGT v5.0 (PyQt6)')
        self.setGeometry(100, 100, 800, 650) # x, y, largura, altura

        # Define uma paleta de cores para um visual minimalista e moderno
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(240, 242, 245)) # Fundo cinza muito claro
        palette.setColor(QPalette.WindowText, QColor(30, 30, 30)) # Texto escuro
        self.setPalette(palette)

        # Layout principal vertical
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(50, 50, 50, 50) # Margens internas generosas
        main_layout.setSpacing(40) # Espaçamento entre os blocos principais

        # --- Cabeçalho Minimalista ---
        header_layout = QHBoxLayout()
        title_label = QLabel('Robo DIGT <span style="font-weight:bold; color:#4C72E0;">v5.0</span>')
        title_label.setFont(QFont('Inter', 32, QFont.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title_label)
        main_layout.addLayout(header_layout)

        # Subtítulo discreto
        subtitle_label = QLabel('<span style="font-size:15px; color:#6B7280;">Automação inteligente e eficiente com Playwright/Asyncio</span>')
        subtitle_label.setFont(QFont('Inter', 11))
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(subtitle_label)

        # --- Área de Conteúdo em Grade (Cards) ---
        content_grid_layout = QGridLayout()
        content_grid_layout.setHorizontalSpacing(30)
        content_grid_layout.setVerticalSpacing(30)
        content_grid_layout.setAlignment(Qt.AlignmentFlag.AlignCenter) # Centraliza a grade

        # --- Card de Seleção de Tarefa ---
        task_card = QFrame()
        task_card.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 20px;
                box-shadow: 0 8px 30px rgba(0, 0, 0, 0.1);
                padding: 30px;
            }
        """)
        task_layout = QVBoxLayout(task_card)
        task_layout.setSpacing(18)
        task_layout.addWidget(QLabel('<span style="font-size:20px; font-weight:bold; color:#333;">Definir Tarefa</span>'), alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        task_label = QLabel('Selecione a tarefa a ser executada:')
        task_label.setFont(QFont('Inter', 13))
        task_layout.addWidget(task_label, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        self.task_combo = QComboBox()
        self.task_combo.addItems(['Atendimento Hipertenso', 'Agendamento Consultas', 'Relatórios Diários', 'Processamento de Dados'])
        self.task_combo.setFont(QFont('Inter', 13))
        self.task_combo.setStyleSheet("""
            QComboBox {
                padding: 14px;
                border: 1px solid #E0E0E0; /* Borda cinza clara */
                border-radius: 15px;
                background-color: #F8F9FA; /* Fundo off-white */
                selection-background-color: #D6E4FF; /* Azul claro na seleção */
                color: #333;
            }
            QComboBox::drop-down {
                border: 0px;
            }
            QComboBox::down-arrow {
                image: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyMCAyMCIgZmlsbD0iY3VycmVudENvbG9yIiBhcmlhLWhpZGRlbj0idHJ1ZSI+PHBhdGggZmlsbFJ1bGU9ImV2ZW5vZGQiIGQ9Ik01LjI5MyA3LjI5M2ExIDEgMCAwMTEuNDE0IDBMMTAgMTAuNTg2bDMuMjkzLTMuMjkzYTEgMSAwIDExMS40MTQgMS40MTRsLTQgNGExIDEgMCAwMS0xLjQxNCAwTDUuMjkzIDguNzA3YTEgMSAwIDAxMC0xLjQxNHoiIGNsaXBSdWxlPSJldmVub2RkIi8+PC9zdmc+);
                width: 22px;
                height: 22px;
                margin-right: 12px;
            }
        """)
        task_layout.addWidget(self.task_combo)
        task_layout.addStretch()

        content_grid_layout.addWidget(task_card, 0, 0)

        # --- Card de Entrada de Data ---
        date_card = QFrame()
        date_card.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 20px;
                box-shadow: 0 8px 30px rgba(0, 0, 0, 0.1);
                padding: 30px;
            }
        """)
        date_layout = QVBoxLayout(date_card)
        date_layout.setSpacing(18)
        date_layout.addWidget(QLabel('<span style="font-size:20px; font-weight:bold; color:#333;">Configurar Data</span>'))

        date_input_label = QLabel('Insira a data para a operação:')
        date_input_label.setFont(QFont('Inter', 13))
        date_layout.addWidget(date_input_label)

        date_input_row_layout = QHBoxLayout()
        self.date_input = QLineEdit()
        self.date_input.setPlaceholderText('DD/MM/YYYY')
        self.date_input.setFont(QFont('Inter', 13))
        self.date_input.setStyleSheet("""
            QLineEdit {
                padding: 14px;
                border: 1px solid #E0E0E0;
                border-radius: 15px;
                background-color: #F8F9FA;
                color: #333;
            }
        """)
        self.date_input.setText(QDate.currentDate().toString('dd/MM/yyyy'))
        date_input_row_layout.addWidget(self.date_input)

        save_data_button = QPushButton('Salvar Data')
        save_data_button.setFont(QFont('Inter', 12, QFont.Weight.DemiBold))
        save_data_button.setStyleSheet("""
            QPushButton {
                background-color: #28A745; /* Verde Bootstrap */
                color: white;
                padding: 14px 25px;
                border-radius: 15px;
                border: none;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1E7E34;
            }
        """)
        save_data_button.clicked.connect(self.save_data)
        date_input_row_layout.addWidget(save_data_button)
        date_layout.addLayout(date_input_row_layout)
        date_layout.addStretch()

        content_grid_layout.addWidget(date_card, 0, 1)

        # --- Card de Opções e Ações ---
        actions_card = QFrame()
        actions_card.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 20px;
                box-shadow: 0 8px 30px rgba(0, 0, 0, 0.1);
                padding: 30px;
            }
        """)
        actions_layout = QVBoxLayout(actions_card)
        actions_layout.setSpacing(25)
        actions_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.delete_csv_checkbox = QCheckBox('Apagar dados.csv após conclusão?')
        self.delete_csv_checkbox.setFont(QFont('Inter', 13))
        self.delete_csv_checkbox.setStyleSheet("""
            QCheckBox {
                spacing: 12px;
                color: #333;
            }
            QCheckBox::indicator {
                width: 26px;
                height: 26px;
                border: 1px solid #D1D5DB;
                border-radius: 10px;
                background-color: #F8F9FA;
            }
            QCheckBox::indicator:checked {
                background-color: #4C72E0; /* Azul principal */
                border: 1px solid #4C72E0;
                image: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0iI0ZGRkZGRiI+PHBhdGggZD0iTTEwLjQ3IDE2Ljc4Yy0uMzkuMzktMS4wMi4zOS0xLjQxIDBsLTMuNzUtMy43NWMtLjM5LS4zOS0uMzktMS4wMiAwLTEuNDFsMS40MS0xLjQxYy4zOS0uMzkgMS4wMi0uMzkgMS40MSAwTDEwLjQ3IDEyLjU4bDUuOTYtNS45NmMuMzktLjM5IDEuMDItLjM5IDEuNDEgMGwxLjQxIDEuNDFjLjM5LjM5LjM5IDEuMDIgMCAxLjQxbC03LjM3IDcuMzdjLS4zOS4zOS0xLjAyLjM5LTEuNDEgMHoiLz48L3N2Z24+);
            }
        """)
        actions_layout.addWidget(self.delete_csv_checkbox, alignment=Qt.AlignmentFlag.AlignCenter)

        start_automation_button = QPushButton('Iniciar Automação')
        start_automation_button.setFont(QFont('Inter', 18, QFont.Weight.Bold))
        start_automation_button.setFixedSize(360, 75)
        start_automation_button.setStyleSheet("""
            QPushButton {
                background-color: #4C72E0; /* Azul principal */
                color: white;
                border-radius: 20px;
                border: none;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
            }
            QPushButton:hover {
                background-color: #3A63CC;
            }
            QPushButton:pressed {
                background-color: #2E52B8;
            }
        """)
        start_automation_button.clicked.connect(self.start_automation)
        actions_layout.addWidget(start_automation_button, alignment=Qt.AlignmentFlag.AlignCenter)

        exit_button = QPushButton('Exit')
        exit_button.setFont(QFont('Inter', 14, QFont.Weight.DemiBold))
        exit_button.setFixedSize(220, 55)
        exit_button.setStyleSheet("""
            QPushButton {
                background-color: #E9ECEF; /* Cinza claro */
                color: #495057; /* Cinza escuro */
                border-radius: 18px;
                border: none;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            }
            QPushButton:hover {
                background-color: #DEE2E6;
            }
            QPushButton:pressed {
                background-color: #CED4DA;
            }
        """)
        exit_button.clicked.connect(self.exit_app)
        actions_layout.addWidget(exit_button, alignment=Qt.AlignmentFlag.AlignCenter)
        actions_layout.addStretch()

        content_grid_layout.addWidget(actions_card, 1, 0, 1, 2) # Linha 1, Coluna 0, Ocupa 1 linha, 2 colunas

        main_layout.addLayout(content_grid_layout)

        # --- Rodapé Minimalista ---
        footer_layout = QHBoxLayout()
        footer_layout.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft)
        footer_layout.setContentsMargins(0, 30, 0, 0) # Margem superior para separar do conteúdo

        copyright_label = QLabel('Copyright DIGT and Клех')
        copyright_label.setFont(QFont('Inter', 11))
        copyright_label.setStyleSheet("color: #6C757D;")
        footer_layout.addWidget(copyright_label)

        footer_layout.addStretch()

        pec_version_label = QLabel('PEC: <span style="font-weight:bold; color:#6C757D;">Versão 5.3.19</span>')
        pec_version_label.setFont(QFont('Inter', 11))
        footer_layout.addWidget(pec_version_label)

        app_version_label = QLabel('App Version: <span style="font-weight:bold; color:#4C72E0;">5.0</span>')
        app_version_label.setFont(QFont('Inter', 11))
        footer_layout.addWidget(app_version_label)

        main_layout.addLayout(footer_layout)

        self.setLayout(main_layout)

    def show_message(self, title, message):
        """Exibe uma caixa de mensagem personalizada."""
        msg_box = QMessageBox()
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setFont(QFont('Inter', 11))
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: white;
                border-radius: 15px;
                padding: 30px;
            }
            QMessageBox QLabel {
                color: #333;
            }
            QMessageBox QPushButton {
                background-color: #4C72E0; /* Azul principal */
                color: white;
                padding: 12px 20px;
                border-radius: 10px;
                border: none;
            }
            QMessageBox QPushButton:hover {
                background-color: #3A63CC;
            }
        """)
        msg_box.exec()

    def save_data(self):
        """Manipulador para o botão 'Salvar Data'."""
        date = self.date_input.text()
        self.show_message('Salvar Data', f'Data "{date}" salva com sucesso!')
        print(f'Data saved: {date}')

    def start_automation(self):
        """Manipulador para o botão 'Iniciar Automação'."""
        task = self.task_combo.currentText()
        date = self.date_input.text()
        delete_csv = self.delete_csv_checkbox.isChecked()
        self.show_message(
            'Automação Iniciada',
            f'A automação para "{task}" foi iniciada com a data "{date}".\nApagar CSV após conclusão: {"Sim" if delete_csv else "Não"}'
        )
        print(f'Automation started: Task="{task}", Date="{date}", Delete CSV={delete_csv}')

    def exit_app(self):
        """Manipulador para o botão 'Exit'."""
        self.show_message('Sair da Aplicação', 'Fechando o Robo DIGT. Até a próxima!')
        print('Exiting application')
        QApplication.instance().quit() # Fecha a aplicação

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = RoboDIGTAppV5()
    ex.show()
    sys.exit(app.exec())
