# Arquivo: app/data/file_manager.py (VERSÃO v1b - Ordenação de Arquivos)
import pandas as pd
import os
import json
import shutil
import sys
import re
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

    def _natural_sort_key(self, filename: str):
        """
        Gera uma chave para ordenação "natural", tratando números dentro de strings como números.
        Ex: "dados1.csv", "dados2.csv", ..., "dados10.csv"
        """
        # Extrai a parte numérica do nome do arquivo (ex: "dados10.csv" -> 10)
        # Se não encontrar número, usa -1 para colocar no início (útil para "dados.csv")
        match = re.search(r'(\d+)\.csv$', filename)
        return int(match.group(1)) if match else -1

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

    def find_next_file_to_process(self) -> Path | None:
        """
        Encontra o próximo arquivo dados*.csv na pasta de arquivos que ainda não foi processado.
        Prioriza 'dados.csv' da raiz, depois os arquivos na subpasta em ordem numérica.
        """
        processed_files = self._load_processed_registry()

        # 1. Verificar dados.csv na raiz de data_input
        main_data_file_name = "dados.csv"
        main_data_file_path = self.DATA_DIR / main_data_file_name
        if main_data_file_path.exists() and main_data_file_name not in processed_files:
            logger.info(f"Próximo arquivo a processar encontrado: {main_data_file_name}")
            return main_data_file_path

        # 2. Listar e ordenar arquivos na subpasta 'arquivos'
        # --- ALTERAÇÃO AQUI: Usando a chave de ordenação natural ---
        files_in_archive_dir = [
            f.name for f in (self.DATA_DIR / "arquivos").iterdir() 
            if f.is_file() and f.name.startswith('dados') and f.name.lower().endswith('.csv')
        ]
        # Ordena usando a nova função _natural_sort_key
        files_in_archive_dir_sorted = sorted(files_in_archive_dir, key=self._natural_sort_key)
        # --- FIM DA ALTERAÇÃO ---

        for filename in files_in_archive_dir_sorted: # Itera sobre a lista ORDENADA
            if filename not in processed_files:
                logger.info(f"Próximo arquivo a processar encontrado: {filename}")
                return (self.DATA_DIR / "arquivos" / filename)
        
        logger.info("Nenhum arquivo dados*.csv não processado encontrado.")
        return None


    def load_data_file(self, file_path: Path):
        """Carrega os dados de um arquivo CSV específico."""
        if not file_path.exists():
            logger.error(f"Arquivo de dados não encontrado: {file_path}")
            return None
        try:
            # Adiciona dtype={1: str} para garantir que o CPF seja lido como string
            df = pd.read_csv(file_path, sep=';', encoding='ISO-8859-1', header=None, dtype=str)
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
        Conta todos os arquivos de dados que ainda não foram marcados como processados,
        usando a mesma lógica de ordenação.
        """
        processed_files = self._load_processed_registry()
        all_unprocessed_names_found = []

        # 1. Verificar "dados.csv" na raiz de data_input
        main_data_file_name = "dados.csv"
        main_data_file_path = self.DATA_DIR / main_data_file_name
        if main_data_file_path.exists() and main_data_file_name not in processed_files:
            all_unprocessed_names_found.append(main_data_file_name)
        
        # 2. Verificar arquivos na subpasta 'arquivos' (e ordenar)
        files_in_archive_dir = [
            f.name for f in (self.DATA_DIR / "arquivos").iterdir() 
            if f.is_file() and f.name.startswith('dados') and f.name.lower().endswith('.csv')
        ]
        # --- ALTERAÇÃO AQUI: Usando a chave de ordenação natural ---
        files_in_archive_dir_sorted = sorted(files_in_archive_dir, key=self._natural_sort_key)
        # --- FIM DA ALTERAÇÃO ---

        for filename in files_in_archive_dir_sorted: # Itera sobre a lista ORDENADA
            if filename not in processed_files:
                all_unprocessed_names_found.append(filename)
        
        return len(all_unprocessed_names_found)