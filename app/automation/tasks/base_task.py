# Arquivo: app/automation/tasks/base_task.py (VERSÃO v1g - Integrando Gênero ACS)
from abc import ABC, abstractmethod # Usamos ABC para criar classes abstratas
from playwright.async_api import Page, Locator
import pandas as pd
from app.core.logger import logger
from app.core.errors import AutomationError # Capturaremos AutomationError também
from app.automation.error_handler import AutomationErrorHandler, SkipRecordException, AbortAutomationException # Importamos o handler e as exceções de controle
import asyncio
import sys
from datetime import datetime # Importa datetime para fallback

# Importa as classes de páginas que serão usadas pelas tarefas filhas (no topo)
from app.automation.pages.login_page import LoginPage
from app.automation.pages.main_menu import MainMenu
from app.automation.pages.common_forms import CommonForms
from app.automation.pages.atendimento_form import AtendimentoForm
from app.automation.pages.procedimento_form import ProcedimentoForm
from app.automation.pages.acs_form import AcsForm

# Importar FileManager e DateSequencer (no topo)
from app.data.file_manager import FileManager
from app.data.date_sequencer import DateSequencer

# Importar a função de normalização (no topo)
from app.core.utils import normalize_text_for_selection


class BaseTask(ABC): # Herda de ABC para ser uma classe abstrata
    """
    Classe base abstrata para todas as tarefas de automação.
    Gerencia o loop pelos dados e o tratamento de exceções de controle.
    Controla o fluxo de processamento de múltiplos arquivos de dados.
    """
    
    def __init__(self, page: Page, error_handler: AutomationErrorHandler, manual_login: bool):
        # Contadores totais da sessão (acumulados em todos os arquivos)
        self._processed_count_total = 0
        self._skipped_count_total = 0

        self._page = page # Instância da página Playwright
        self._handler = error_handler # Instância do gerenciador de erros
        self._manual_login = manual_login # Armazena o parâmetro de login manual
        
        # Instâncias das classes de páginas (instanciadas no __init__ da Task)
        self._login_page = LoginPage(self._page, self._handler)
        self._main_menu = MainMenu(self._page, self._handler)
        self._common_forms = CommonForms(self._page, self._handler)
        self._atendimento_form = AtendimentoForm(self._page, self._handler)
        self._procedimento_form = ProcedimentoForm(self._page, self._handler)
        self._acs_form = AcsForm(self._page, self._handler)
        # Variável para guardar a instância do iframe (será definida após navegação inicial)
        self._current_iframe_frame: Locator = None

    async def _perform_pre_navigation_steps(self):
        """
        Gancho para seleção de perfil. A implementação padrão tenta selecionar 'ENFERMEIRO'.
        Tarefas específicas (como a do ACS) podem sobrescrever este método.
        """
        logger.info("Executando passo de pré-navegação padrão: Tentando selecionar perfil 'ENFERMEIRO'.")
        profile_selected = await self._login_page.select_profile_and_unidade_optional(
            profile_name_to_select="ENFERMEIRO"
        )
        if not profile_selected:
            logger.warning("Não foi possível selecionar o perfil 'ENFERMEIRO' automaticamente. A automação continuará com o perfil que já estiver carregado.")
        else:
            logger.info("Perfil 'ENFERMEIRO' selecionado com sucesso.")

    async def run(self):
        """
        Executa a tarefa de automação para todos os arquivos de dados não processados.
        Gerencia o login, a navegação inicial, o loop pelos arquivos e o loop pelos registros.
        """
        logger.info(f"Iniciando execução da tarefa: {self.__class__.__name__}")

        # Instanciar FileManager e DateSequencer (aqui no run, pois são específicos do fluxo de arquivos)
        file_manager = FileManager()
        date_sequencer = DateSequencer()


        try:
            # --- Passo 1: Login e Seleção Inicial (comum a todas as tarefas) ---
            from app.data.config_loader import ConfigLoader
            config_loader = ConfigLoader()
            config = config_loader.load_config()
            if not config:
                raise AutomationError("Falha ao carregar configurações de login.")

            await self._login_page.navigate_and_login(config["url"], config["usuario"], config["senha"])
            # profile_and_unidade_selected = await self._login_page.select_profile_and_unidade_optional() # <--- REMOVER ESTA LINHA
            # if not profile_and_unidade_selected: # <--- REMOVER ESTE BLOCO IF COMPLETO
            #     logger.warning("Perfil/Unidade de Enfermeiro NÃO selecionado. A automação pode falhar nos próximos passos.")


            # --- Passo 2: Lógica Condicional de Login Manual vs. Automático ---
            if self._manual_login: # <-- NOVO BLOCO LÓGICO
                logger.warning("LOGIN MANUAL ATIVADO. Pausando por 5 segundos para seleção de perfil/equipe.")
                logger.warning("Por favor, selecione seu perfil e equipe na tela do e-SUS AGORA.")
                await asyncio.sleep(5) # Pausa de 10 segundos
                logger.info("Pausa concluída. Continuando com a automação...")
            else:
                # Se não for manual, executa a seleção automática de perfil
                await self._perform_pre_navigation_steps()
            # --- FIM DA NOVA LÓGICA ---

            # --- Passo 2a. Navegação para a tela da Ficha (Atendimento ou Procedimento) ---
            # _navigate_to_task_area retorna o FrameLocator do iframe principal APÓS navegar no menu.
            # Esta navegação acontece UMA VEZ POR SESSÃO (não por arquivo).
            self._current_iframe_frame = await self._navigate_to_task_area()

            if not self._current_iframe_frame:
                 raise AutomationError("Falha ao navegar para a área específica da tarefa.")


            # --- Passo 3: Gerenciar a Sequência de Arquivos e Datas ---
            # Lógica para contar quantos arquivos não processados existem e gerar datas para eles.
            main_date_initial_from_file = file_manager.load_main_date_file()
            if not main_date_initial_from_file:
                 logger.warning("Não foi possível carregar a data principal de data.csv para geração de sequência. Usando data atual.")
                 main_date_initial_from_file = datetime.now().strftime('%d/%m/%Y') # Fallback


            num_unprocessed_files_total = file_manager.count_all_unprocessed_files() # Método em FileManager

            if num_unprocessed_files_total > 0:
                 # GERA a sequência de datas. O PRIMEIRO item da sequência PODE SER o main_date_initial_from_file.
                 date_sequence_for_session = date_sequencer.generate_sequence_dates(
                     num_dates=num_unprocessed_files_total,
                     start_date_override=main_date_initial_from_file # Passa a data do data.csv para a geração
                 )
                 logger.info(f"Sequência de datas gerada/obtida para {num_unprocessed_files_total} arquivos: {date_sequence_for_session}")

                 if len(date_sequence_for_session) < num_unprocessed_files_total:
                      logger.warning(f"Número de datas geradas/obtidas ({len(date_sequence_for_session)}) é menor que o número de arquivos ({num_unprocessed_files_total}). Alguns arquivos podem não ter data.")

            else:
                 logger.info("Nenhum arquivo de dados a processar nesta sessão.")
                #  await self._browser_manager.close_browser()
                #  self.finished.emit("Nenhum arquivo para processar")
                 return


            # --- Passo 4: Loop WHILE encontrar arquivos a processar ---
            # Este loop continua ENQUANTO find_next_file_to_process encontrar arquivos.
            current_data_file_path = file_manager.find_next_file_to_process() # Pega o primeiro arquivo real


            while current_data_file_path: # Loop principal por arquivos
                 logger.info(f"Iniciando processamento do arquivo: {current_data_file_path.name}")

                 # 4a. Obter a data correspondente para ESTE arquivo.
                 current_main_date_for_file = date_sequencer.get_next_sequence_date()
                 if not current_main_date_for_file:
                     logger.error(f"Sequência de datas esgotada inesperadamente para o arquivo {current_data_file_path.name}. Pulando este e próximos arquivos.")
                     break # Sai do loop de arquivos

                 logger.info(f"Usando a data '{current_main_date_for_file}' para o arquivo '{current_data_file_path.name}'.")


                 # 4b. Carregar os dados do arquivo CSV atual
                 data_df_current_file = file_manager.load_data_file(current_data_file_path) # Usar novo nome para data_df
                 if data_df_current_file is None or data_df_current_file.empty:
                     logger.warning(f"Arquivo de dados vazio ou com erro: {current_data_file_path.name}. Pulando.")
                     file_manager.mark_file_as_processed(current_data_file_path)
                     current_data_file_path = file_manager.find_next_file_to_process()
                     continue # Pula para a próxima iteração do loop while (próximo arquivo)


                 # --- 4c. CLICAR NO BOTÃO "Adicionar" para abrir a primeira ficha DESTE ARQUIVO ---
                 # Este clique acontece UMA VEZ POR ARQUIVO (após entrar na tela da ficha).
                 logger.info("Clicando no botão 'Adicionar' na tela da ficha para abrir a primeira ficha vazia deste arquivo.")
                 add_initial_clicked_successful = False # Flag para retentativa manual deste clique
                 while not add_initial_clicked_successful:
                      try:
                          await self._main_menu.click_add_button_in_iframe(self._current_iframe_frame) # CLICA ADICIONAR INICIAL
                          await asyncio.sleep(1.5) # Espera após o clique Adicionar
                          add_initial_clicked_successful = True # Sucesso

                      except SkipRecordException: raise # Propaga Skip
                      except AbortAutomationException: raise # Propaga Abort
                      except Exception as e:
                           logger.error(f"Erro no clique inicial em 'Adicionar' para o arquivo {current_data_file_path.name}. Tentando novamente após possível correção manual: {e}")
                           await self._handler.handle_error(e, step_description=f"Clique inicial em 'Adicionar' para arquivo {current_data_file_path.name}")
                           # O loop while continuará.


                 # --- 4d. Preencher Data Principal PARA ESTE ARQUIVO ---
                 logger.info(f"Iniciando preenchimento da data principal para este arquivo: {current_main_date_for_file}")
                 # Mover o mouse (opcional, mas útil)
                 page_width = self._page.viewport_size['width'] if self._page.viewport_size else 1280
                 page_height = self._page.viewport_size['height'] if self._page.viewport_size else 720
                 center_x = page_width // 2
                 center_y = page_height // 2
                 logger.debug(f"Movendo mouse para o centro da tela ({center_x}, {center_y})...")
                 await self._page.mouse.move(center_x, center_y)
                 await asyncio.sleep(0.5)
                 logger.debug("Mouse movido.")

                 # Preencher a data
                 await self._common_forms.fill_date_field(self._current_iframe_frame, current_main_date_for_file)
                 logger.info(f"Data principal '{current_main_date_for_file}' preenchida com sucesso para este arquivo.")

                 # ** NOVO PASSO: CLICAR NO BOTÃO "Adicionar" APÓS PREENCHER A DATA PRINCIPAL **
                 # Isso faz o sistema entender que o cabeçalho da ficha foi preenchido
                 # e prepara a área para os dados do PRIMEIRO PACIENTE.
                 logger.info("Clicando em 'Adicionar' para preparar o formulário para o primeiro registro do arquivo.")
                 add_for_first_record_successful = False # Flag para retentativa
                 while not add_for_first_record_successful:
                      try:
                           await self._main_menu.click_add_button_in_iframe(self._current_iframe_frame) # CLICA ADICIONAR
                           await asyncio.sleep(1.5) # Espera o formulário do paciente aparecer
                           add_for_first_record_successful = True
                      except SkipRecordException: raise
                      except AbortAutomationException: raise
                      except Exception as e:
                           logger.error(f"Erro no clique em 'Adicionar' após data principal para arquivo {current_data_file_path.name}. Tentando novamente: {e}")
                           await self._handler.handle_error(e, step_description=f"Clique 'Adicionar' após data principal para arquivo {current_data_file_path.name}")


                 # --- 4e. Loop Principal pelos Registros DESTE ARQUIVO ---
                 # Este loop chama process_row para cada linha do data_df_current_file DESTE arquivo.
                 # E clica "Adicionar" entre os registros (exceto após o último DESTE arquivo).
                 logger.info(f"Iniciando loop de processamento para {len(data_df_current_file)} registros DESTE arquivo.")
                 # Passamos o DataFrame DESTE arquivo para o _process_all_rows.
                 # O _process_all_rows lidará com a iteração pelas linhas e cliques Adicionar entre registros.
                 await self._process_all_rows(data_df_current_file) # Passa o DataFrame DESTE arquivo


                 # --- 4f. Marcar arquivo como processado (após processar TODAS as linhas DESTE arquivo) ---
                 logger.info(f"Todas as linhas do arquivo {current_data_file_path.name} processadas (ou puladas/abortadas).")
                 file_manager.mark_file_as_processed(current_data_file_path)

                 # ** NOVO PASSO: CLICAR EM "FINALIZAR REGISTROS" PARA ESTE ARQUIVO **
                 logger.info(f"Finalizando registros para o arquivo {current_data_file_path.name} (clicando Finalizar registros).")
                 await self._finalize_task() # Chama o método abstrato que clica Finalizar registros
                 logger.info(f"Finalização para o arquivo {current_data_file_path.name} concluída.")

                 # --- 4g. Encontrar o Próximo arquivo para a PRÓXIMA iteração do loop while ---
                 current_data_file_path = file_manager.find_next_file_to_process()


            # --- Passo 5: Finalizar Lote (Após TODOS os arquivos serem processados) ---
            logger.info(f"Loop principal de arquivos finalizado. Total de registros processados na sessão: {self._processed_count_total}, pulados: {self._skipped_count_total}.")
            logger.info("Sessão de automação concluída. Todos os arquivos foram processados e finalizados.")
            # await self._finalize_task() # Chama o método abstrato que agora clicará Finalizar registros

            logger.info(f"Execução da tarefa '{self.__class__.__name__}' concluída.")        

        except (AbortAutomationException, Exception) as e:
            logger.error(f"Automação abortada ou erro fatal durante a tarefa '{self.__class__.__name__}': {e}")


    # --- _process_all_rows AGORA RECEBE data_df COMO PARÂMETRO ---
    async def _process_all_rows(self, data_df_this_file: pd.DataFrame): # Agora recebe o DataFrame como parâmetro
        """
        Itera sobre o DataFrame recebido e processa cada linha.
        Lida com pulo de registro e retentativa manual para process_row e clique Adicionar (entre registros).
        """
        total_rows_this_file = len(data_df_this_file) # Usa o tamanho do DataFrame DESTE arquivo

        for index, row in data_df_this_file.iterrows(): # Itera sobre o DataFrame DESTE arquivo
            logger.info(f"Iniciando processamento do registro {index + 1}/{total_rows_this_file} do arquivo atual.") # Log ajustado
            data_row = [None if pd.isna(x) else x for x in row.tolist()]

            # ** Loop de retentativa manual para process_row (preencher e confirmar) **
            process_row_successful = False
            while not process_row_successful:
                 try:
                     logger.debug(f"Tentativa para processar (preencher e confirmar) registro {index + 1}.")
                     # Chama o método abstrato que a tarefa filha implementa (preenche e clica Confirmar)
                     # process_row só retorna se o clique Confirmar for bem-sucedido e não gerar popup message-box
                     await self.process_row(self._current_iframe_frame, data_row) # PREENCHE E CLICA CONFIRMAR

                     # ** SE CHEGOU AQUI, process_row FOI CONCLUÍDO COM SUCESSO REAL **
                     # self._processed_count_total += 1 # Não incrementa aqui mais
                     logger.info(f"Processamento da linha {index + 1} concluído com sucesso.")
                     process_row_successful = True # Sucesso no process_row, sai deste loop while


                 except SkipRecordException:
                     # Captura Skip no process_row (preenchimento/confirmar)
                     self._skipped_count_total += 1 # Contagem total
                     logger.warning(f"Registro {index + 1} pulado conforme solicitação do usuário.")
                     process_row_successful = True # Pulado, sai deste loop while (e não tentará o clique Adicionar abaixo para esta linha)

                 except AbortAutomationException:
                     # Captura Abort no process_row
                     logger.error(f"Automação abortada pelo usuário no registro {index + 1}.")
                     raise # Re-levanta para sair do loop de registros principal (`for index, row in ...`)

                 # ** TRATAMENTO GENÉRICO PARA EXCEÇÕES DENTRO DE process_row **
                 except Exception as e:
                      # Captura QUALQUER outra exceção que ocorra DENTRO de process_row.
                      # O handle_error JÁ foi chamado e você interagiu (clicou "Continue").
                      logger.error(f"Erro não tratado ou não recuperável em process_row para registro {index + 1}. Tentando novamente após possível correção manual: {e}")
                      # O loop while (while not process_row_successful:) continuará.
                      # Não faz nada aqui exceto logar. Não conta como skipped ainda.
                      await asyncio.sleep(1) # Pausa antes de retentar o process_row


            # ** Clicar no botão "Adicionar" para o próximo registro (SE process_row FOI BEM-SUCEDIDO E NÃO É O ÚLTIMO DESTE ARQUIVO) **
            # Este bloco SÓ SERÁ EXECUTADO SE process_row_successful FOR TRUE (ou seja, não pulou nem abortou em process_row)
            # E SE NÃO É O ÚLTIMO REGISTRO DO ARQUIVO ATUAL.
            # Se for o ÚLTIMO registro DESTE arquivo, NÃO clica Adicionar.
            if process_row_successful and index < total_rows_this_file - 1: # Usa total_rows_this_file na condição
                 add_clicked_successful = False
                 while not add_clicked_successful: # Loop de retentativa manual PARA O CLIQUE EM ADICIONAR
                      try:
                          logger.info(f"Registro {index + 1}/{total_rows_this_file} processado com sucesso. Tentando clicar em 'Adicionar' para o próximo registro ({index + 2}).")
                          await self._main_menu.click_add_button_in_iframe(self._current_iframe_frame) # CLICA ADICIONAR ENTRE REGISTROS
                          await asyncio.sleep(2) # Espera após o clique Adicionar
                          add_clicked_successful = True # Sucesso no clique Adicionar
                          # Incrementa o processed_count total APENAS após processar a linha E clicar Adicionar (se necessário e não for o último)
                          self._processed_count_total += 1


                      except SkipRecordException:
                           # Captura Skip no clique Adicionar
                           self._skipped_count_total += 1 # Contagem total
                           logger.warning(f"Clique em 'Adicionar' após registro {index + 1} pulado conforme solicitação do usuário.")
                           add_clicked_successful = True # Considera "sucesso" para sair deste loop while e ir para a próxima linha do CSV.

                      except AbortAutomationException:
                           # Captura Abort no clique Adicionar
                           logger.error(f"Automação abortada pelo usuário no clique em 'Adicionar' após registro {index + 1}.")
                           raise # Re-levanta para sair do loop principal


                      # ** TRATAMENTO GENÉRICO PARA EXCEÇÕES DENTRO DO CLIQUE ADICIONAR **
                      except Exception as e:
                           # Captura QUALQUER outra exceção que ocorra DENTRO do try (APENAS o clique Adicionar).
                           logger.error(f"Erro no clique em 'Adicionar' após registro {index + 1}. Tentando novamente após possível correção manual: {e}")
                           # O loop while (while not add_clicked_successful:) continuará.
                           await asyncio.sleep(1) # Pausa antes de retentar o clique Adicionar


            # ** Se for o último registro deste arquivo (index == total_rows_this_file - 1) **
            # Não clica Adicionar. O loop for index termina.
            # Precisamos incrementar o processed_count para o último registro aqui.
            if process_row_successful and index == total_rows_this_file - 1:
                 # Incrementa o processed_count total para o último registro deste arquivo.
                 self._processed_count_total += 1
                 logger.info(f"Último registro ({index + 1}/{total_rows_this_file}) processado. Não clicando em 'Adicionar'.")


    @abstractmethod
    async def _navigate_to_task_area(self) -> Locator:
        """
        Método abstrato que as classes filhas devem implementar para navegar
        até a área específica da tarefa (Atendimento Individual ou Procedimentos)
        e retornar a instância do frame principal.
        """
        pass # Implementação real estará nas classes filhas

    @abstractmethod
    async def process_row(self, iframe_frame: Locator, row_data: list):
        """
        Método abstrato que as classes filhas devem implementar para
        processar uma única linha de dados, interagindo com os campos
        específicos da sua tarefa dentro do iframe.
        Recebe a instância do frame principal e os dados da linha como lista.
        """
        pass # Implementação real estará nas classes filhas

    @abstractmethod
    async def _finalize_task(self):
        """
        Método abstrato que as classes filhas devem implementar para
        finalizar a tarefa após o loop de registros (ex: clicar em Salvar
        ou Finalizar Registros).
        """
        pass # Implementação real estará nas classes filhas

    # Adicione o método auxiliar para preencher dados comuns aqui:
    async def _fill_common_patient_data(self, iframe_frame: Locator, row_data: list):
         """Preenche campos comuns do paciente a partir de uma linha de dados."""
         logger.debug("Preenchendo dados comuns do paciente...")
         # Assume que as colunas 0 a 4 do CSV são:
         # 0: Periodo (str)
         # 1: CPF/CNS (str)
         # 2: Data Nasc (str)
         # 3: Sexo (int: 1=Masc, 2=Fem, 3=Indet)
         # 4: Local Atendimento (str)

         # Verifique se row_data tem tamanho suficiente antes de acessar índices
         if len(row_data) > 0:
             await self._common_forms.select_period(iframe_frame, str(row_data[0]))
         if len(row_data) > 1:
             await self._common_forms.fill_cpf_cns(iframe_frame, str(row_data[1]))
         if len(row_data) > 2:
             await self._common_forms.fill_date_of_birth(iframe_frame, str(row_data[2]))
         if len(row_data) > 3:
             # Converte para int com tratamento básico de erro
             try:
                  gender_int = int(row_data[3])
                  await self._common_forms.select_gender_02(iframe_frame, gender_int)
             except (ValueError, TypeError):
                  logger.warning(f"Valor inválido para Gênero na linha: {row_data[3]}. Pulando seleção de gênero.")
         if len(row_data) > 4:
             await self._common_forms.select_local_atendimento_02(iframe_frame, str(row_data[4]))

         # Pausa opcional após preencher campos comuns
         # await asyncio.sleep(1)
    # --- NOVA FUNÇÃO PARA PREENCHER DADOS DO ACS ---
    async def _fill_common_patient_acs(self, iframe_frame: Locator, row_data: list):
        """Preenche campos comuns do paciente para a ficha de Visita Domiciliar do ACS."""
        logger.debug("Preenchendo dados comuns do paciente (ACS)...")
        # Assume que as colunas 0, 1, 2, 3, 4 e 9 do CSV são:
        # 0: Periodo (str)
        # 1: CPF/CNS (str)
        # 2: Data Nasc (str)
        # 3: Sexo (int: 1=Masc, 2=Fem, 3=Indet)
        # 4: Microárea (str or int)
        # 8: Tipo de imóvel (código, ex: "01")

        # Reutiliza a lógica já existente para os campos compartilhados
        if len(row_data) > 0:
            await self._common_forms.select_period(iframe_frame, str(row_data[0]))
        if len(row_data) > 1:
            await self._common_forms.fill_cpf_cns(iframe_frame, str(row_data[1]))
        if len(row_data) > 2:
            await self._common_forms.fill_date_of_birth(iframe_frame, str(row_data[2]))
        if len(row_data) > 3:
            try:
                gender_int = int(row_data[3])
                await self._acs_form.select_gender_acs(iframe_frame, gender_int) # Teste clica sexo ACS
            except (ValueError, TypeError):
                logger.warning(f"Valor inválido para Gênero na linha: {row_data[3]}. Pulando seleção.")

        # --- ALTERAÇÃO: Chamando os novos métodos do acs_form.py ---
        if len(row_data) > 4:
            # Chama o método que criamos em acs_form.py
            await self._acs_form.fill_micro_area(iframe_frame, str(row_data[4]))
        if len(row_data) > 8:
            # Chama o método de seleção, passando o código do CSV e o texto esperado.
            # Assumindo que o código '01' sempre corresponde a 'DOMICÍLIO'
            imovel_code = str(row_data[8])
            imovel_description = "DOMICÍLIO" # Pode ser adaptado se houver outros tipos
            await self._acs_form.select_tipo_imovel(iframe_frame, imovel_code, imovel_description)
    # --- FIM DA NOVA FUNÇÃO ---