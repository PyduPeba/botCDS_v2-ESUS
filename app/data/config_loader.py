# Arquivo: app/data/config_loader.py
import pandas as pd
import sys
from pathlib import Path
from app.core.logger import logger

class ConfigLoader:
    # Determina o diretório base do aplicativo (funciona para script e executável)
    if getattr(sys, 'frozen', False):
        BASE_DIR = Path(sys.executable).parent
    else:
        BASE_DIR = Path(__file__).resolve().parents[2]

    CONFIG_FILE = BASE_DIR / "resources" / "config" / "configuracao.csv"

    def load_config(self):
        """Carrega configurações de URL, usuário e senha do CSV."""
        if not self.CONFIG_FILE.exists():
            logger.error(f"Arquivo de configuração não encontrado: {self.CONFIG_FILE}")
            return None # Retorna None se o arquivo não existir

        try:
            # Lê o CSV sem cabeçalho, esperando 3 linhas
            df = pd.read_csv(self.CONFIG_FILE, header=None, nrows=3)
            if df.shape[0] < 3:
                 logger.error(f"Arquivo de configuração incompleto: {self.CONFIG_FILE}. Esperado 3 linhas (URL, Usuário, Senha).")
                 return None

            url = df.iloc[0, 0] if not pd.isna(df.iloc[0, 0]) else ""
            usuario = df.iloc[1, 0] if not pd.isna(df.iloc[1, 0]) else ""
            senha = df.iloc[2, 0] if not pd.isna(df.iloc[2, 0]) else ""

            logger.info("Configurações de login carregadas com sucesso.")
            return {"url": url, "usuario": usuario, "senha": senha}

        except FileNotFoundError:
             logger.error(f"Arquivo de configuração não encontrado: {self.CONFIG_FILE}")
             return None
        except Exception as e:
            logger.error(f"Erro ao carregar arquivo de configuração {self.CONFIG_FILE}: {e}")
            return None

# Exemplo de uso:
if __name__ == '__main__':
    loader = ConfigLoader()
    config = loader.load_config()
    if config:
        print("Configurações carregadas:", config)
    else:
        print("Falha ao carregar configurações.")