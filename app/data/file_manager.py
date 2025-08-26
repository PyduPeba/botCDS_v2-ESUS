# Arquivo: app/data/file_manager.py (CORRIGIDO 50 - PARTE 0)
import pandas as pd
import os
import json
import shutil
import sys
from pathlib import Path
from app.core.logger import logger
from app.core.app_config import AppConfig # Para verificar a configuração de apagar arquivo

class FileManager:
    # Determina o diretório base do aplicativo
    if getattr(sys, 'frozen', False):
        BASE_DIR = Path(sys.executable).parent
    else:
        BASE_DIR = Path(__file__).resolve().parents[2]

    DATA_DIR = BASE_DIR / "resources" / "data_input"
    ARCHIVE_DIR = DATA_DIR / "arquivos_processados" # Nova pasta para arquivos arquivados
    PROCESSED_REGISTRY = DATA_DIR / "arquivos" / "registro.json" # Mantém o registro onde já estava

    def __init__(self):
        # Garante que as pastas de dados e arquivo existam
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
        self.PROCESSED_REGISTRY.parent.mkdir(parents=True, exist_ok=True) # Garante a pasta do registro

    def _is_file_processed(self, filename: str) -> bool:
        """Verifica se um arquivo (pelo nome) já está registrado como processado."""
        processed_files = self._load_processed_registry()
        return filename in processed_files


    def _load_processed_registry(self):
        """Carrega a lista de arquivos já processados."""
        if not self.PROCESSED_REGISTRY.exists():
            return []
        try:
            with open(self.PROCESSED_REGISTRY, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Erro ao carregar registro de arquivos processados {self.PROCESSED_REGISTRY}: {e}")
            return [] # Retorna lista vazia em caso de erro

    def _save_processed_registry(self, processed_files):
        """Salva a lista atualizada de arquivos processados."""
        try:
            with open(self.PROCESSED_REGISTRY, 'w', encoding='utf-8') as f:
                json.dump(processed_files, f, indent=4)
        except IOError as e:
            logger.error(f"Erro ao salvar registro de arquivos processados {self.PROCESSED_REGISTRY}: {e}")

    def find_next_file_to_process(self) -> Path: # Retorna Path ou None
        """
        Encontra o próximo arquivo dados*.csv na pasta de arquivos
        que ainda não foi processado. Prioriza 'dados.csv' da raiz se não processado.
        """
        processed_files = self._load_processed_registry()

        # 1. Verificar dados.csv na raiz de data_input
        main_data_file_name = "dados.csv"
        main_data_file_path = self.DATA_DIR / main_data_file_name
        if main_data_file_path.exists() and main_data_file_name not in processed_files:
            logger.info(f"Próximo arquivo a processar encontrado: {main_data_file_name}")
            return main_data_file_path # Retorna o Path completo

        # 2. Listar arquivos na subpasta 'arquivos' (se dados.csv já foi processado ou não existe)
        files_in_archive_dir = sorted([f.name for f in (self.DATA_DIR / "arquivos").iterdir() if f.is_file() and f.name.startswith('dados') and f.name.lower().endswith('.csv')])

        for filename in files_in_archive_dir:
            if filename not in processed_files:
                logger.info(f"Próximo arquivo a processar encontrado: {filename}")
                return (self.DATA_DIR / "arquivos" / filename) # Retorna o Path completo
        
        logger.info("Nenhum arquivo dados*.csv não processado encontrado.")
        return None # Nenhum arquivo novo encontrado


    def load_data_file(self, file_path: Path):
        """Carrega os dados de um arquivo CSV específico."""
        if not file_path.exists():
            logger.error(f"Arquivo de dados não encontrado: {file_path}")
            return None
        try:
            # Adiciona dtype={1: str} para garantir que o CPF seja lido como string
            df = pd.read_csv(file_path, sep=';', encoding='ISO-8859-1', header=None, dtype={1: str})
            logger.info(f"Arquivo de dados carregado com sucesso: {file_path.name}")
            return df
        except FileNotFoundError:
             logger.error(f"Arquivo de dados não encontrado: {file_path}")
             return None
        except Exception as e:
            logger.error(f"Erro ao carregar arquivo de dados {file_path}: {e}")
            return None

    def mark_file_as_processed(self, file_path: Path):
        """Adiciona o arquivo ao registro de processados e o move/deleta conforme config."""
        processed_files = self._load_processed_registry()
        filename = file_path.name

        if filename not in processed_files:
            processed_files.append(filename)
            self._save_processed_registry(processed_files)
            logger.info(f"Arquivo {filename} marcado como processado.")

        # Lida com o arquivo fisicamente (move ou deleta)
        if AppConfig.delete_file_after_completion:
            try:
                file_path.unlink() # Deleta o arquivo
                logger.info(f"Arquivo {filename} deletado conforme configuração.")
            except Exception as e:
                logger.error(f"Erro ao deletar arquivo {filename}: {e}")
        else:
            try:
                archive_path = self.ARCHIVE_DIR / filename
                shutil.move(str(file_path), str(archive_path)) # Move o arquivo
                logger.info(f"Arquivo {filename} movido para {self.ARCHIVE_DIR}.")
            except shutil.Error as e:
                logger.warning(f"Arquivo {filename} já existe em {self.ARCHIVE_DIR} ou erro ao mover: {e}")
            except Exception as e:
                logger.error(f"Erro inesperado ao mover arquivo {filename}: {e}")


    def load_main_date_file(self):
        """Carrega a data principal do arquivo data.csv."""
        date_file = self.DATA_DIR / "data.csv"
        if not date_file.exists():
            logger.error(f"Arquivo de data principal não encontrado: {date_file}")
            return None
        try:
            df = pd.read_csv(date_file, header=None)
            if df.empty or df.shape[0] < 2 or df.shape[1] == 0:
                logger.error(f"Arquivo de data principal incompleto ou vazio: {date_file}. Esperado cabeçalho + 1 linha de dados.")
                return None
            date_str = str(df.iloc[1, 0]).strip()
            logger.info(f"Data principal carregada: {date_str}")
            return date_str
        except Exception as e:
            logger.error(f"Erro ao carregar data principal de {date_file}: {e}")
            return None
    
    # ** NOVO MÉTODO: CONTA TODOS OS ARQUIVOS DE DADOS NÃO PROCESSADOS **
    def count_all_unprocessed_files(self) -> int:
        """
        Conta todos os arquivos de dados (dados.csv na raiz e dados*.csv na subpasta arquivos)
        que ainda não foram marcados como processados.
        """
        processed_files = self._load_processed_registry()
        all_unprocessed_names_found = []

        # 1. Verificar "dados.csv" na raiz de data_input
        main_data_file_name = "dados.csv"
        main_data_file_path = self.DATA_DIR / main_data_file_name
        if main_data_file_path.exists() and main_data_file_name not in processed_files:
            all_unprocessed_names_found.append(main_data_file_name)
        
        # 2. Verificar arquivos na subpasta 'arquivos'
        # Ordenar para garantir ordem consistente se for o caso.
        for f in sorted((self.DATA_DIR / "arquivos").iterdir()):
            if (f.is_file() and 
                f.name.startswith('dados') and 
                f.name.lower().endswith('.csv') and 
                f.name not in processed_files):
                all_unprocessed_names_found.append(f.name)
        
        return len(all_unprocessed_names_found) # Retorna a contagem