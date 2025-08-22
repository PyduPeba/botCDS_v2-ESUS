# Arquivo: app/core/app_config.py
import json
import os
import sys
from pathlib import Path

class AppConfig:
    # Determina o diretório base do aplicativo (funciona para script e executável)
    if getattr(sys, 'frozen', False):
        # Se rodando como executável (PyInstaller)
        BASE_DIR = Path(sys.executable).parent
    else:
        # Se rodando como script Python
        # O caminho do config.py é app/core/, então subimos 3 níveis para chegar na raiz do projeto
        BASE_DIR = Path(__file__).resolve().parents[2]

    CONFIG_FILE = BASE_DIR / "resources" / "config" / "config.json"

    # Valores padrão da configuração
    delete_file_after_completion = False
    # Adicione outras configurações globais aqui conforme necessário

    @staticmethod
    def load_config():
        """Carrega as configurações do arquivo JSON."""
        if not AppConfig.CONFIG_FILE.exists():
            print(f"Arquivo de configuração não encontrado em: {AppConfig.CONFIG_FILE}. Criando com valores padrão.")
            AppConfig.save_config() # Cria o arquivo se não existir
            return

        try:
            with open(AppConfig.CONFIG_FILE, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                # Carrega cada configuração, usando o valor padrão se não encontrar no arquivo
                AppConfig.delete_file_after_completion = config_data.get('delete_file_after_completion', AppConfig.delete_file_after_completion)
                # Carregar outras configurações aqui
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Erro ao carregar arquivo de configuração {AppConfig.CONFIG_FILE}: {e}")
            # Opcional: Resetar para valores padrão em caso de erro de leitura
            AppConfig.delete_file_after_completion = False
            print("Configurações redefinidas para os valores padrão.")


    @staticmethod
    def save_config():
        """Salva as configurações atuais para o arquivo JSON."""
        config_data = {
            'delete_file_after_completion': AppConfig.delete_file_after_completion,
            # Salvar outras configurações aqui
        }
        try:
            # Garante que a pasta config existe
            AppConfig.CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(AppConfig.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4)
        except IOError as e:
            print(f"Erro ao salvar arquivo de configuração {AppConfig.CONFIG_FILE}: {e}")

# Carrega a configuração inicial quando o módulo é importado
AppConfig.load_config()

if __name__ == '__main__':
    # Exemplo de uso e teste
    print(f"Caminho do arquivo de configuração: {AppConfig.CONFIG_FILE}")
    print(f"Valor inicial de delete_file_after_completion: {AppConfig.delete_file_after_completion}")

    # Altera uma configuração e salva
    AppConfig.set_delete_file_after_completion(True)
    print(f"Valor alterado: {AppConfig.delete_file_after_completion}")

    # Recarrega para verificar
    AppConfig.load_config()
    print(f"Valor após recarregar: {AppConfig.delete_file_after_completion}")

    # Função auxiliar para ser chamada da GUI
    @staticmethod
    def set_delete_file_after_completion(value: bool):
        AppConfig.delete_file_after_completion = value
        AppConfig.save_config()