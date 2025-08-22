# Arquivo: app/data/date_sequencer.py (CORRIGIDO 56 - PARTE 1)
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from app.core.logger import logger

class DateSequencer:
    # Determina o diretório base do aplicativo
    if getattr(sys, 'frozen', False):
        BASE_DIR = Path(sys.executable).parent
    else:
        BASE_DIR = Path(__file__).resolve().parents[2]

    REGISTRY_FILE = BASE_DIR / "resources" / "data_input" / "arquivos" / "dataseqregistro.json"

    def __init__(self):
        # Garante que a pasta do registro existe
        self.REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
        self._load_state()

    def _load_state(self):
        """Carrega o estado de datas do arquivo JSON."""
        if not self.REGISTRY_FILE.exists():
            logger.info(f"Arquivo de registro de datas não encontrado em: {self.REGISTRY_FILE}. Inicializando com estado padrão.")
            self._state = {'datas_usadas': [], 'datas_seq': [], 'datas_a_ignorar': [], 'ultima_data_usada': None}
            self._save_state() # Cria o arquivo com estado inicial
            return

        try:
            with open(self.REGISTRY_FILE, 'r', encoding='utf-8') as f:
                self._state = json.load(f)
                # Garante que as chaves existem, mesmo que vazias
                self._state.setdefault('datas_usadas', [])
                self._state.setdefault('datas_seq', [])
                self._state.setdefault('datas_a_ignorar', [])
                # 'ultima_data_usada' pode ser None
            logger.info("Estado do sequenciador de datas carregado.")
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Erro ao carregar estado do sequenciador de datas {self.REGISTRY_FILE}: {e}")
            # Em caso de erro, inicializa o estado para evitar problemas futuros
            self._state = {'datas_usadas': [], 'datas_seq': [], 'datas_a_ignorar': [], 'ultima_data_usada': None}
            logger.warning("Estado do sequenciador de datas resetado devido a erro de leitura.")


    def _save_state(self):
        """Salva o estado atual das datas para o arquivo JSON."""
        try:
            with open(self.REGISTRY_FILE, 'w', encoding='utf-8') as f:
                json.dump(self._state, f, indent=4)
            # logger.debug("Estado do sequenciador de datas salvo.") # Pode gerar muito log se salvar frequentemente
        except IOError as e:
            logger.error(f"Erro ao salvar estado do sequenciador de datas {self.REGISTRY_FILE}: {e}")

    def _is_weekend(self, date: datetime):
        """Verifica se uma data é final de semana."""
        return date.weekday() > 4 # 5 = Sábado, 6 = Domingo
    # Método auxiliar _proxima_data_util precisa receber a lista de datas a evitar
    def _proxima_data_util(self, data_inicial: datetime, dates_to_avoid_str: set):
        """Encontra a próxima data útil (não final de semana ou na lista a ignorar)."""
        data = data_inicial
        # A lista a ignorar deve conter strings no formato "dd/mm/YYYY"
        while True:
            data += timedelta(days=1)
            data_str = data.strftime('%d/%m/%Y')
            if data_str not in dates_to_avoid_str and not self._is_weekend(data):
                break
        return data # Retorna objeto datetime

    #Antiga geração de datas mais está usar a 1 data como base no primeiro arquivo.
    # def generate_sequence_dates(self, num_dates: int, start_date_str: str = None):
    #     """
    #     Gera uma sequência de 'num_dates' datas úteis.
    #     Se 'start_date_override' for fornecida e a sequência interna estiver vazia,
    #     usa-a como a primeira data da sequência (se for útil) ou como ponto de partida.
    #     """
    #     # Se já houver datas na sequência, não gera novas a menos que a contagem não seja suficiente
    #     if len(self._state.get('datas_seq', [])) >= num_dates:
    #          logger.info("Sequência de datas já existente é suficiente.")
    #          return self._state['datas_seq'][:num_dates] # Retorna apenas o número necessário

    #     # Determina a data de início da geração
    #     if start_date_str:
    #         try:
    #             current_date = datetime.strptime(start_date_str, '%d/%m/%Y')
    #             logger.info(f"Iniciando geração de sequência a partir da data fornecida: {start_date_str}")
    #         except ValueError:
    #             logger.error(f"Formato inválido para start_date_str: {start_date_str}. Usando a última data usada no registro.")
    #             current_date = self._get_last_used_date_obj() # Usa a última data usada

    #     elif self._state.get('ultima_data_usada'):
    #         current_date = self._get_last_used_date_obj()
    #         logger.info(f"Iniciando geração de sequência a partir da última data usada no registro: {self._state['ultima_data_usada']}")
    #     else:
    #         # Se não houver start_date_str nem ultima_data_usada, começa a partir de hoje
    #         current_date = datetime.today()
    #         logger.warning("Nenhuma data inicial ou última data usada encontrada. Iniciando geração de sequência a partir de hoje.")

    #     new_sequence = []
    #     dates_to_avoid_str = set(self._state.get('datas_a_ignor', []) + self._state.get('datas_usadas', []) + self._state.get('datas_seq', []))

    #     for _ in range(num_dates - len(self._state.get('datas_seq', []))): # Gera apenas as datas que faltam
    #          # Encontra a próxima data útil, evitando as já usadas/a ignorar/na sequência
    #          while True:
    #             current_date += timedelta(days=1)
    #             date_str = current_date.strftime('%d/%m/%Y')
    #             if date_str not in dates_to_avoid_str and not self._is_weekend(current_date):
    #                 new_sequence.append(date_str)
    #                 dates_to_avoid_str.add(date_str) # Adiciona à lista de datas a evitar para as próximas iterações
    #                 break # Sai do loop while e vai para a próxima data na sequência

    #     self._state['datas_seq'].extend(new_sequence) # Adiciona as novas datas geradas à sequência existente
    #     self._save_state()
    #     logger.info(f"Sequência de {len(self._state['datas_seq'])} datas gerada/atualizada.")
    #     return self._state['datas_seq']

    def generate_sequence_dates(self, num_dates: int, start_date_override: str = None) -> list:
        """
        Gera uma sequência de 'num_dates' datas úteis.
        Se 'start_date_override' for fornecida e a sequência interna estiver vazia,
        usa-a como a primeira data da sequência (se for útil) ou como ponto de partida.
        """
        # Se já houver datas na sequência e for suficiente, retorna a existente.
        if len(self._state.get('datas_seq', [])) >= num_dates:
             logger.info("Sequência de datas já existente é suficiente.")
             return self._state['datas_seq'][:num_dates]

        new_sequence = []
        
        # Determina o ponto de partida para a GERAÇÃO
        if start_date_override:
            try:
                start_gen_date_obj = datetime.strptime(start_date_override, '%d/%m/%Y')
                logger.info(f"Usando data de override '{start_date_override}' para iniciar a geração da sequência.")
            except ValueError:
                logger.error(f"Formato inválido para start_date_override: {start_date_override}. Ignorando override.")
                start_gen_date_obj = self._get_last_used_date_obj() # Fallback
        elif self._state.get('ultima_data_usada'):
            start_gen_date_obj = self._get_last_used_date_obj()
            logger.info(f"Usando 'ultima_data_usada' '{self._state['ultima_data_usada']}' para iniciar a geração da sequência.")
        else:
            start_gen_date_obj = datetime.today()
            logger.warning("Nenhuma data inicial ou última data usada encontrada. Iniciando geração a partir de hoje.")
        
        current_date = start_gen_date_obj # Inicia com a data determinada

        dates_to_avoid_str = set(self._state.get('datas_a_ignorar', []) + self._state.get('datas_usadas', []) + self._state.get('datas_seq', []))

        # Se a sequência está vazia e temos uma data de override que ainda não foi usada,
        # podemos considerar essa data como o primeiro item da sequência, se ela for útil.
        # Caso contrário, geramos a partir do próximo dia útil.
        if not self._state.get('datas_seq') and start_date_override:
            start_date_override_normalized = datetime.strptime(start_date_override, '%d/%m/%Y')
            start_date_override_str = start_date_override_normalized.strftime('%d/%m/%Y')

            # Verifica se a data de override já é um dia útil e não está na lista de datas a evitar
            if not self._is_weekend(start_date_override_normalized) and start_date_override_str not in dates_to_avoid_str:
                new_sequence.append(start_date_override_str)
                dates_to_avoid_str.add(start_date_override_str) # Adiciona para evitar duplicidade
                current_date = start_date_override_normalized # O próximo cálculo começará a partir dela.
                logger.debug(f"Adicionando '{start_date_override_str}' como primeira data da sequência (override).")
            else:
                logger.debug(f"Data de override '{start_date_override_str}' não é útil ou já está em uso. Gerando a partir do próximo dia útil.")
                # Se a data de override não puder ser a primeira, o current_date já está setado para ela,
                # e o loop abaixo vai para o próximo dia útil.
        
        # Gera as datas restantes até atingir num_dates
        # Se new_sequence já tem um item (o override), gera num_dates - 1 a partir do próximo.
        # Se new_sequence está vazia, gera num_dates a partir do próximo dia útil após current_date.
        while len(new_sequence) < num_dates:
            current_date = self._proxima_data_util(current_date, dates_to_avoid_str) # Encontra a próxima data útil
            date_str = current_date.strftime('%d/%m/%Y')
            
            if date_str not in dates_to_avoid_str: # Dupla verificação
                new_sequence.append(date_str)
                dates_to_avoid_str.add(date_str) # Adiciona à lista de datas a evitar para próximas iterações
            else:
                # Isso não deveria acontecer se _proxima_data_util está correto,
                # mas é uma salvaguarda para evitar loops infinitos se _proxima_data_util falhar.
                logger.warning(f"Data '{date_str}' já está na lista a evitar, pulando para a próxima tentativa.")
                current_date += timedelta(days=1) # Tenta a próxima data imediatamente

        self._state['datas_seq'].extend(new_sequence)
        self._save_state()
        logger.info(f"Sequência de {len(self._state['datas_seq'])} datas gerada/atualizada.")
        return self._state['datas_seq']

    def get_next_sequence_date(self):
        """
        Retorna a próxima data da sequência e a remove da lista de datas_seq.
        Marca esta data como a 'ultima_data_usada'.
        """
        if not self._state.get('datas_seq'):
            logger.warning("Sequência de datas está vazia. Não é possível obter a próxima data.")
            return None

        next_date_str = self._state['datas_seq'].pop(0) # Remove a primeira data da sequência
        self._state['datas_usadas'].append(next_date_str) # Adiciona às datas usadas
        self._state['ultima_data_usada'] = next_date_str # Atualiza a última data usada
        self._save_state()
        logger.info(f"Próxima data da sequência utilizada: {next_date_str}")
        return next_date_str

    def _get_last_used_date_obj(self):
        """Retorna a última data usada como objeto datetime."""
        last_date_str = self._state.get('ultima_data_usada')
        if last_date_str:
            try:
                return datetime.strptime(last_date_str, '%d/%m/%Y')
            except ValueError:
                logger.error(f"Formato inválido para ultima_data_usada no registro: {last_date_str}. Usando data de hoje como fallback.")
                return datetime.today()
        else:
             logger.info("Nenhuma 'ultima_data_usada' encontrada no registro. Usando data de hoje como fallback.")
             return datetime.today()


# Exemplo de uso:
if __name__ == '__main__':
    # Limpa o registro para um teste limpo
    # if DateSequencer.REGISTRY_FILE.exists():
    #     DateSequencer.REGISTRY_FILE.unlink()

    ds = DateSequencer()

    # Carregar data principal para iniciar a sequência (simula a leitura do data.csv)
    # Você deve carregar isso do FileManager na aplicação real
    fm_test = FileManager()
    main_date_str = fm_test.load_main_date_file() # Suponha que 'data.csv' tenha '01/04/2025'

    # Simula que encontrou 3 arquivos adicionais (dados1.csv, dados2.csv, dados3.csv)
    num_files_to_process = 3

    # Gere a sequência de datas com base na data principal (ou última usada se já existir)
    sequence = ds.generate_sequence_dates(num_files_to_process, start_date_str=main_date_str)
    print(f"Sequência de datas gerada: {sequence}")
    print(f"Estado atual (após gerar): {ds._state}")


    # Simula o processamento de um arquivo
    print("\nSimulando processamento de 3 arquivos:")
    for i in range(num_files_to_process):
        next_date = ds.get_next_sequence_date()
        if next_date:
            print(f"  Arquivo {i+1}: Processando com a data {next_date}")
            # Na aplicação real, você usaria essa data para preencher o campo de data no formulário

    print(f"\nEstado final (após usar datas): {ds._state}")

    # Tente gerar mais datas (não deve gerar se o número for menor ou igual ao total usado + sequencia)
    print("\nTente gerar mais 2 datas (total 5):")
    sequence_again = ds.generate_sequence_dates(5, start_date_str=main_date_str)
    print(f"Sequência de datas gerada novamente: {sequence_again}") # Deve gerar mais 2 datas
    print(f"Estado atual (após gerar novamente): {ds._state}")

    # Teste ignorar datas (adicione manualmente ao dataseqregistro.json para testar)
    # Edite resources/data_input/arquivos/dataseqregistro.json e adicione em "datas_a_ignorar": ["dd/mm/YYYY", ...]