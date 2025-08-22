# Arquivo: app/core/logger.py
import logging
import os
import sys
from pathlib import Path
from datetime import datetime

# Determina o diretório base do aplicativo
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).resolve().parents[2]

LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True) # Garante que a pasta de logs existe

# Define o formato da mensagem de log
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# Define o nome do arquivo de log diário
LOG_FILE = LOG_DIR / f"botcds_{datetime.now().strftime('%Y-%m-%d')}.log"

# Configura o logger raiz
logging.basicConfig(
    level=logging.INFO, # Nível mínimo de log a ser registrado (INFO, DEBUG, WARNING, ERROR, CRITICAL)
    format=LOG_FORMAT,
    datefmt=DATE_FORMAT,
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'), # Salva logs em arquivo
        logging.StreamHandler(sys.stdout) # Exibe logs no console
    ]
)

# Cria um logger específico para o seu aplicativo
logger = logging.getLogger("BotCDS")
logger.setLevel(logging.DEBUG) # Você pode definir um nível de detalhe diferente para o logger do app

# Exemplo de uso:
if __name__ == "__main__":
    logger.debug("Esta é uma mensagem de debug.")
    logger.info("Esta é uma mensagem informativa.")
    logger.warning("Esta é uma mensagem de aviso.")
    logger.error("Esta é uma mensagem de erro.")
    logger.critical("Esta é uma mensagem crítica.")