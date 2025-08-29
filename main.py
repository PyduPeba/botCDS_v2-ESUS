# Arquivo: main.py
import sys
from PyQt5.QtWidgets import QApplication

# Importa a janela principal da camada GUI
from app.gui.main_window import MainWindow

# Importa a configuração do aplicativo para garantir que seja carregada
from app.core.app_config import AppConfig

# Importa o logger para garantir que a configuração inicial seja aplicada v
from app.core.logger import logger

if __name__ == '__main__':
    # Carrega as configurações do aplicativo (incluindo caminho base)
    # Isso já é feito na importação do AppConfig, mas chamar explicitamente garante.
    AppConfig.load_config()
    logger.info("Aplicação iniciada.")
    logger.info(f"Diretório base do aplicativo: {AppConfig.BASE_DIR}")

    # Cria a instância da aplicação PyQt
    app = QApplication(sys.argv)

    # Cria a janela principal
    main_window = MainWindow()

    # Exibe a janela
    main_window.show()

    # Garante que a aplicação PyQt saia de forma limpa quando a janela principal for fechada
    # A MainWindow já tem um método exit_app conectado ao botão, mas fechar a janela com o X
    # também deve encerrar a aplicação.
    # app.aboutToQuit.connect(main_window.exit_app) # Descomentado se exit_app não chamar QApplication.quit()

# Inicia o loop de eventos do PyQt
sys.exit(app.exec_())