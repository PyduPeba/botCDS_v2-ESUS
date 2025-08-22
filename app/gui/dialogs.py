# Arquivo: app/gui/dialogs.py
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QApplication, QWidget)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QByteArray, QBuffer, QIODevice, QTimer
from app.core.errors import AutomationError # Importamos nossa exceção de erro

import base64 # Para encodar a imagem em base64 se necessário (alternativa a caminho de arquivo)
from pathlib import Path

class ErrorDialog(QDialog):
    """
    Diálogo exibido quando um erro de automação ocorre e a automação é pausada.
    Permite ao usuário escolher entre Continuar, Pular Registro ou Abortar Automação.
    """
    def __init__(self, error: AutomationError, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Erro de Automação Detectado")
        self.setModal(True) # Torna a janela modal (bloqueia outras interações na janela principal)
        # ** ADICIONA FLAGS PARA FICAR NO TOPO **
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        # Pode adicionar outras flags como remover botões de minimizar/maximizar se quiser uma janela mais simples
        # self.setWindowFlags(self.windowFlags() | Qt.WindowTitleHint | Qt.CustomizeWindowHint | Qt.WindowCloseButtonHint)

        self.result = "abort" # Resultado padrão caso a janela seja fechada

        layout = QVBoxLayout()

        # Mensagem de erro
        error_message_label = QLabel(f"Um erro ocorreu durante a automação:")
        layout.addWidget(error_message_label)

        # Campo de texto para mostrar os detalhes do erro
        self.error_details_textedit = QTextEdit()
        self.error_details_textedit.setReadOnly(True)
        self.error_details_textedit.setPlainText(str(error)) # Mostra os detalhes formatados da exceção
        layout.addWidget(self.error_details_textedit)

        # Mostrar Screenshot (se disponível)
        if error.screenshot_path and Path(error.screenshot_path).exists():
            screenshot_label = QLabel("Screenshot no momento do erro:")
            layout.addWidget(screenshot_label)

            # Exibe a imagem
            pixmap = QPixmap(error.screenshot_path)
            # Redimensiona para caber no diálogo, mantendo a proporção
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(600, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation) # Ajuste o tamanho máximo
                self.screenshot_display = QLabel()
                self.screenshot_display.setPixmap(scaled_pixmap)
                self.screenshot_display.setAlignment(Qt.AlignCenter)
                layout.addWidget(self.screenshot_display)
            else:
                 layout.addWidget(QLabel(f"Erro ao carregar screenshot: {error.screenshot_path}"))

        # Botões de Ação
        button_layout = QHBoxLayout()

        self.continue_button = QPushButton("Continuar (Após correção manual)")
        self.continue_button.clicked.connect(self.accept_continue)
        button_layout.addWidget(self.continue_button)

        self.skip_button = QPushButton("Pular Registro")
        self.skip_button.clicked.connect(self.accept_skip)
        button_layout.addWidget(self.skip_button)

        self.abort_button = QPushButton("Abortar Automação")
        self.abort_button.clicked.connect(self.reject_abort) # Usamos reject para o comportamento padrão de fechar com X
        button_layout.addWidget(self.abort_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)

        # Ajusta o tamanho inicial do diálogo
        self.resize(800, 600) # Tamanho inicial, será ajustado pelo layout

    def accept_continue(self):
        """Define o resultado como 'continue' e fecha o diálogo."""
        self.result = "continue"
        self.accept() # Chama o método aceitar do QDialog

    def accept_skip(self):
        """Define o resultado como 'skip' e fecha o diálogo."""
        self.result = "skip"
        self.accept() # Chama o método aceitar do QDialog

    def reject_abort(self):
        """Define o resultado como 'abort' e fecha o diálogo."""
        self.result = "abort"
        self.reject() # Chama o método rejeitar do QDialog (equivale a fechar a janela com X)

    def get_result(self):
        """Retorna a ação escolhida pelo usuário."""
        return self.result