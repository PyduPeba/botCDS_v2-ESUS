# Arquivo: app/gui/worker.py
from PyQt5.QtCore import QThread, pyqtSignal, QObject, QMetaObject, Qt # Importa os componentes PyQt para threading e signals
import asyncio
import traceback # Para capturar o stack trace
import sys
from pathlib import Path
import pandas as pd

# Importa as classes da lógica de automação e dados
from app.automation.browser import BrowserManager
from app.automation.error_handler import AutomationErrorHandler, SkipRecordException, AbortAutomationException
# Importe as classes das suas Tarefas específicas aqui
from app.automation.tasks.atend_hipertenso_task import AtendimentoHipertensoTask
from app.automation.tasks.atend_diabetico_task import AtendimentoDiabeticoTask
from app.automation.tasks.atend_a97_task import AtendimentoA97Task
from app.automation.tasks.proce_afericao_task import ProcedimentoAfericaoTask
from app.automation.tasks.proce_saude_repro_task import ProcedimentoSaudeReproTask
from app.automation.tasks.atend_saude_repro_task import AtendimentoSaudeReproTask # Nova tarefa incluída
from app.automation.tasks.hipertenso_procedimento_task import HipertensoProcedimentoTask # A tarefa combinada
from app.automation.tasks.proce_diabetes_task import ProcedimentoDiabeticoTask
from app.data.file_manager import FileManager
from app.data.date_sequencer import DateSequencer
from app.core.app_config import AppConfig # Para verificar a configuração de apagar arquivo
from app.core.logger import logger
from app.core.errors import AutomationError # Importa para capturar no nível do worker
from app.gui.dialogs import ErrorDialog # Importa o diálogo de erro

# Define um dicionário para mapear o tipo de tarefa selecionado na GUI
# para a classe da tarefa correspondente
TASK_MAP = {
    "Atendimento Hipertenso": AtendimentoHipertensoTask,
    "Atendimento Diabetico": AtendimentoDiabeticoTask,
    "Atendimento SEM DOENÇA": AtendimentoA97Task,
    "Atendimento Saúde Sexual": AtendimentoSaudeReproTask, # Nova tarefa incluída
    "Procedimentos Aferição": ProcedimentoAfericaoTask,
    "Procedimento Sáude Sexual": ProcedimentoSaudeReproTask,
    "Procedimento Diabéticos": ProcedimentoDiabeticoTask, 
    "Hipertenso e Procedimento": HipertensoProcedimentoTask,
    # Adicione outras tarefas aqui
}


class Worker(QObject):
    """
    Objeto que roda a lógica assíncrona da automação dentro de uma QThread.
    Usa sinais para se comunicar com a GUI principal.
    """
    # Sinais que o Worker emitirá para a GUI principal
    # Argumentos dos sinais devem ser tipos que o Qt consegue serializar ou objetos Python comuns
    finished = pyqtSignal(str) # Sinal emitido quando a automação termina (sucesso ou falha)
    error_occurred = pyqtSignal(AutomationError) # Sinal emitido quando um erro de automação ocorre (para pausar)
    # progress_update = pyqtSignal(str) # Opcional: sinal para atualizar uma barra de progresso ou log na GUI

    def __init__(self, task_type: str, parent=None):
        super().__init__(parent)
        self._task_type = task_type
        self._browser_manager = BrowserManager()
        self._error_handler: AutomationErrorHandler = None # Será inicializado mais tarde
        self._file_manager = FileManager()
        self._date_sequencer = DateSequencer()
        self._user_action_event = asyncio.Event() # Evento para esperar a ação do usuário do diálogo
        self._user_action = None # Armazena a ação escolhida pelo usuário ('continue', 'skip', 'abort')

    def run_automation(self):
        """
        Este método é o ponto de entrada para a thread. Ele roda o loop asyncio.
        """
        logger.info("Worker thread iniciada. Rodando loop asyncio...")
        try:
            # Rodamos a lógica assíncrona principal
            asyncio.run(self._async_run())
        except Exception as e:
            # Captura qualquer exceção que possa escapar do _async_run
            logger.critical(f"Exceção fatal no loop asyncio do Worker: {e}", exc_info=True)
            self.finished.emit(f"Erro fatal: {e}") # Sinaliza a GUI que terminou com erro
        finally:
             logger.info("Worker thread finalizada.")
             # O sinal finished.emit() já foi chamado no _async_run ou na captura acima.
             # Nada mais a fazer aqui no final.

    async def _async_run(self):
        """Lógica principal assíncrona que inicia o navegador e a tarefa."""
        page = None # Inicializa page como None
        try:
            # -- Passo 1: Iniciar o Navegador --
            # Rodar headless (sem janela) ou não? Pode ser uma opção na GUI
            # Por enquanto, True para não abrir janela por padrão, mude para False para debug
            headless = False # TODO: Fazer isso ser uma opção na GUI

            page = await self._browser_manager.launch_browser(headless=headless)

            # -- Passo 2: Inicializar o ErrorHandler com o callback --
            # O callback precisa chamar um método na thread principal da GUI (MainWindow)
            # que exibirá o diálogo. Usaremos QMetaObject.invokeMethod para isso.
            self._error_handler = AutomationErrorHandler(page, pause_callback=self._handle_pause_request_from_handler)

            # -- Passo 3: Carregar Dados e Configurações --
            # Carrega a data principal do data.csv
            main_date = self._file_manager.load_main_date_file()
            if not main_date:
                 raise AutomationError("Não foi possível carregar a data principal de data.csv")

            # Encontra o primeiro arquivo dados*.csv a processar
            current_data_file = self._file_manager.find_next_file_to_process()

            # -- Passo 4: Loop de Processamento de Arquivos/Lotes --
            while current_data_file:
                 logger.info(f"Iniciando processamento do arquivo: {current_data_file.name}")

                 # Carrega os dados do arquivo CSV atual
                 data_df = self._file_manager.load_data_file(current_data_file)
                 if data_df is None or data_df.empty:
                     logger.warning(f"Arquivo de dados vazio ou com erro: {current_data_file.name}. Pulando.")
                     # Marcar como processado mesmo que vazio para não re-processar
                     self._file_manager.mark_file_as_processed(current_data_file)
                     current_data_file = self._file_manager.find_next_file_to_process() # Tenta o próximo arquivo
                     continue # Pula para a próxima iteração do loop while

                 # -- Passo 5: Preparar e Rodar a Tarefa --
                 TaskClass = TASK_MAP.get(self._task_type)
                 if not TaskClass:
                     raise AutomationError(f"Tipo de tarefa desconhecido: {self._task_type}")

                 logger.info(f"Criando instância da tarefa: {TaskClass.__name__}")
                 # Passa a página, o handler, o DataFrame e a data principal para a instância da tarefa
                 task_instance = TaskClass(page, self._error_handler, data_df, main_date)

                 # -- Passo 6: Executar a Tarefa Principal --
                 await task_instance.run() # A tarefa.run() contém o loop pelos registros do DataFrame

                 # -- Passo 7: Marcar arquivo como processado e verificar o próximo --
                 logger.info(f"Tarefa para o arquivo {current_data_file.name} concluída.")
                 self._file_manager.mark_file_as_processed(current_data_file)

                 # Verifica se há mais arquivos a processar (lógica de sequência)
                 # Aqui você pode usar o DateSequencer para gerar datas para os próximos arquivos
                 # ou simplesmente verificar se find_next_file_to_process retorna algo.
                 # A lógica de gerenciar a sequência de datas deve ser integrada aqui se a
                 # tarefa precisar de datas diferentes para arquivos subsequentes.

                 # Para a lógica simples de "processar todos os dados*.csv na pasta arquivos",
                 # basta chamar find_next_file_to_process novamente. O DateSequencer pode
                 # ser usado para *gerar* as datas *antes* de iniciar o Worker, ou
                 # a task pode pedir a próxima data para cada arquivo.
                 # Vamos manter a lógica do DateSequencer separada da busca de arquivos por enquanto.
                 # O DateSequencer gera as datas e as Tasks usam a data do data.csv (que pode ser atualizado pelo DateSequencer).

                 # Encontra o próximo arquivo. find_next_file_to_process já usa o registro.json
                 current_data_file = self._file_manager.find_next_file_to_process()

                 if current_data_file:
                      logger.info("Próximo arquivo na sequência encontrado. Continuar loop...")
                      # Se houver um próximo arquivo, talvez a data principal precise ser atualizada
                      # A lógica do DateSequencer DEVE ser chamada ANTES deste loop ou
                      # o DateSequencer DEVE modificar o data.csv para o Worker ler a próxima data.
                      # REVISÃO NECESSÁRIA: A lógica de sequência de datas e arquivos precisa ser mais robusta.
                      # A DateSequencer deve ser chamada pela GUI ANTES de iniciar o Worker,
                      # gerando as datas para todos os arquivos que serão processados nesta sessão.
                      # O Worker então recebe a LISTA de arquivos e a LISTA de datas e as associa.

                      # ALTERNATIVA MAIS SIMPLES POR ORA: O DateSequencer é chamado AQUI no Worker
                      # antes de carregar cada NOVO arquivo (após o primeiro).
                      logger.info("Gerando/obtendo próxima data da sequência para o novo arquivo...")
                      next_main_date = self._date_sequencer.get_next_sequence_date()
                      if next_main_date:
                           # Atualiza a data principal que será passada para a próxima Task
                           main_date = next_main_date
                           logger.info(f"Usando a próxima data da sequência: {main_date}")
                           # IMPORTANTE: O CAMPO DE DATA NA INTERFACE PRECISA SER PREENCHIDO NOVAMENTE
                           # COM ESTA NOVA DATA NO INÍCIO DO PROCESSAMENTO DO NOVO ARQUIVO.
                           # Isso é feito dentro da Task (_async_run chama fill_date_field).
                           pass # A Task usará a 'main_date' atualizada.
                      else:
                           logger.warning("Sequência de datas esgotada ou erro. Terminando loop de arquivos.")
                           break # Sai do loop de arquivos se não houver mais datas

                 else:
                      logger.info("Nenhum arquivo adicional a processar. Loop de arquivos finalizado.")


            # -- Passo Final: Fechamento Limpo --
            logger.info("Automação concluída com sucesso (ou todos os arquivos processados/pulados).")
            await self._browser_manager.close_browser()
            self.finished.emit("Sucesso") # Sinaliza a GUI que terminou com sucesso


        except (SkipRecordException, AbortAutomationException):
            # Estas exceções não devem chegar até aqui no _async_run se o _process_all_rows as capturar
            # e quebrar o loop corretamente. Se chegarem, significa que algo não foi capturado.
             logger.error("Exceção SkipRecordException ou AbortAutomationException escapou do _process_all_rows!")
             await self._browser_manager.close_browser()
             self.finished.emit("Terminada (usuário pulou/abortou)") # Sinaliza que terminou por ação do usuário

        except AutomationError as e:
            # Captura AutomationError que não resultou em Skip/Abort (ex: falha no login, navegação inicial)
            logger.error(f"Erro de automação fatal: {e}")
            if page:
                 try: await page.close() # Tenta fechar a página
                 except: pass
            await self._browser_manager.close_browser()
            self.finished.emit(f"Falha na automação: {e.message}") # Sinaliza a GUI que terminou com erro

        except Exception as e:
            # Captura qualquer outra exceção inesperada que não seja AutomationError
            logger.critical(f"Erro INESPERADO e fatal durante a automação: {e}", exc_info=True)
            if page:
                 try: await page.close() # Tenta fechar a página
                 except: pass
            await self._browser_manager.close_browser()
            self.finished.emit(f"Erro inesperado e fatal: {e}") # Sinaliza a GUI que terminou com erro


    # --- Métodos chamados PELA THREAD PRINCIPAL DA GUI ---
    # Estes métodos são slots (ou chamados via invokeMethod)
    # Eles precisam ser síncronos do ponto de vista da THREAD PRINCIPAL
    # mas interagem com o estado (eventos) da thread do Worker

    def handle_error_from_worker(self, error: AutomationError):
        """
        Slot chamado pela thread do Worker quando um erro de automação ocorre
        e o ErrorHandler solicita uma pausa.
        Este método roda na THREAD PRINCIPAL da GUI.
        """
        logger.info("GUI (Main Thread): Recebido sinal de erro. Exibindo diálogo.")
        # Certifique-se que este método roda na thread da GUI
        if QThread.currentThread() != QApplication.instance().thread():
            # Se por algum motivo não estiver na thread principal, invoca ele mesmo na thread principal
            QMetaObject.invokeMethod(self, 'handle_error_from_worker', Qt.BlockingQueuedConnection,
                                       pyqtSignal(AutomationError).signature(), error)
            return

        # Exibe o diálogo de erro modal
        dialog = ErrorDialog(error)
        # exec_() é bloqueante para a thread que a chama (a thread principal da GUI neste caso)
        # A thread do Worker está esperando em self._user_action_event.wait()
        result_code = dialog.exec_()
        user_action = dialog.get_result()

        logger.info(f"GUI (Main Thread): Usuário escolheu a ação: {user_action}")

        # Armazena a ação escolhida e sinaliza o evento asyncio para que a thread do Worker continue
        self._user_action = user_action
        self._user_action_event.set() # Sinaliza o evento asyncio

    # --- Método de callback usado PELO ErrorHandler (roda na thread do Worker) ---
    def _handle_pause_request_from_handler(self, error: AutomationError) -> str:
        """
        Callback chamado pelo AutomationErrorHandler quando ele precisa pausar.
        Este método roda na THREAD DO WORKER (onde o asyncio está rodando).
        Ele invoca um método na thread principal da GUI para mostrar o diálogo
        e espera que a GUI retorne a ação do usuário.
        """
        logger.info("Worker (Asyncio Thread): Handler solicitou pausa. Notificando GUI...")

        # Limpa o evento antes de sinalizar a GUI, para garantir que ele espere
        self._user_action_event.clear()
        self._user_action = None # Limpa a ação anterior

        # Emite o sinal para a thread principal da GUI exibir o diálogo de erro.
        # Usamos Qt.BlockingQueuedConnection para fazer com que o método na thread principal
        # seja chamado e ESPERE sua execução terminar ANTES que este método _handle_pause_request_from_handler
        # retorne.
        QMetaObject.invokeMethod(self, 'handle_error_from_worker', Qt.BlockingQueuedConnection,
                                 pyqtSignal(AutomationError).signature(), error)

        # Após invokeMethod com BlockingQueuedConnection retornar, a thread principal já processou o diálogo
        # e setou self._user_action e self._user_action_event.set()
        # O AutomationErrorHandler que chamou este callback AGORA pode continuar, e ele
        # verificará self._user_action para saber qual ação o usuário escolheu.
        logger.info(f"Worker (Asyncio Thread): Callback para GUI retornou. Ação do usuário: {self._user_action}")

        # Retorna a ação escolhida pelo usuário de volta para o ErrorHandler
        return self._user_action

# Exemplo de como a MainWindow usaria o Worker (pseudo-código para ilustrar):
#
# class MainWindow(QWidget):
#      def __init__(self):
#           # ... setup GUI ...
#           self.start_button.clicked.connect(self.start_automation)
#
#      def start_automation(self):
#           task_type = self.task_dropdown.currentText() # Pega o tipo de tarefa selecionado
#           # Carrega data principal e arquivos (usando FileManager e DateSequencer)
#           # file_manager = FileManager()
#           # main_date = file_manager.load_main_date_file()
#           # current_file = file_manager.find_next_file_to_process()
#           # data_df = file_manager.load_data_file(current_file)
#
#           # Cria a thread de trabalho
#           self.automation_thread = QThread()
#           # Cria o objeto Worker e o move para a thread
#           self.automation_worker = Worker(task_type) # Passa o tipo de tarefa
#           self.automation_worker.moveToThread(self.automation_thread)
#
#           # Conecta sinais do Worker aos slots na MainWindow
#           self.automation_thread.started.connect(self.automation_worker.run_automation) # Quando a thread inicia, chama run_automation
#           self.automation_worker.finished.connect(self.automation_thread.quit) # Quando o worker termina, para a thread
#           self.automation_worker.finished.connect(self.automation_worker.deleteLater) # Limpa o worker
#           self.automation_thread.finished.connect(self.automation_thread.deleteLater) # Limpa a thread
#           self.automation_worker.finished.connect(self.on_automation_finished) # Ex: exibir mensagem na GUI
#
#           # Conecta o sinal de erro do Worker a um slot que exibirá o diálogo NA THREAD PRINCIPAL
#           self.automation_worker.error_occurred.connect(self.handle_error_dialog_request) # Isso não está certo. O ErrorHandler usa o callback direto.
#           # O callback _handle_pause_request_from_handler JÁ invoca handle_error_from_worker
#           # na thread principal. Então, basta garantir que handle_error_from_worker está no QObject certo
#           # (automation_worker) e que ele se moveu para a thread certa.
#           # A conexão real que precisamos é APENAS o sinal `finished`. O tratamento de erro é interno.
#
#           # Inicia a thread
#           self.automation_thread.start()
#
#      def on_automation_finished(self, result_message):
#           logger.info(f"Automação finalizada. Resultado: {result_message}")
#           # Atualiza a GUI (ex: re-habilita botões, mostra mensagem de sucesso/erro)
#
#      # O método handle_error_from_worker está DENTRO da classe Worker,
#      # mas é invocado via QMetaObject.invokeMethod na thread principal
#      # pelo callback _handle_pause_request_from_handler que roda na thread do worker.
#      # QMetaObject.invokeMethod(self, 'handle_error_from_worker', ...) chama self.handle_error_from_worker
#      # na thread do self (o worker). Precisamos garantir que o worker OBJETIVO está na thread CERTA (a thread separada).
#      # E o método handle_error_from_worker PRECISA rodar na thread principal.
#      # CORREÇÃO: Mover handle_error_from_worker PARA MainWindow ou um QObject dedicado na thread principal.
#      # E o callback _handle_pause_request_from_handler deve chamar ESSE MÉTODO na MainWindow.
#      # Exemplo: self._worker.error_occurred.emit(error) (sinal do Worker para MainWindow)
#      # E MainWindow.handle_error_dialog_request(error) exibirá o diálogo e CHAMARÁ um método no Worker para retomar.
#      # Vamos ajustar! A conexão GUI <-> Worker <-> ErrorHandler <-> Asyncio é o ponto mais tricky.


# Reajustando a lógica de comunicação para usar Sinais PyQt corretamente:
# 1. Worker emite SINAL error_occurred para MainWindow quando o handler precisa pausar.
# 2. MainWindow recebe SINAL, exibe Diálogo.
# 3. Diálogo retorna Ação (continue/skip/abort).
# 4. MainWindow chama MÉTODO (slot) no Worker para informar a ação e retomar.

class Worker(QObject): # QObject move para QThread, não QThread herda de QObject
     """
     Objeto que roda a lógica assíncrona da automação dentro de uma QThread.
     Usa sinais para se comunicar com a GUI principal.
     """
     # Sinais que o Worker emitirá para a GUI principal
     # Usamos `object` como tipo para `error` porque AutomationError não é um tipo Qt
     # e contém objetos Python complexos (como lista, Path). QObject pode serializar
     # mais objetos Python do que tipos básicos.
     finished = pyqtSignal(str)
     # Sinal para pedir que a GUI exiba o diálogo de erro. Emite a AutomationError.
     request_error_dialog = pyqtSignal(object) # Emitirá uma instância de AutomationError

     # Slot que o Worker receberá da GUI (MainWindow) com a ação do usuário
     user_action_received = pyqtSignal(str) # Receberá 'continue', 'skip', ou 'abort'


     def __init__(self, task_type: str):
         super().__init__(None) # Não precisa de parent, vai para a thread

         self._task_type = task_type
         self._browser_manager = BrowserManager()
         self._error_handler: AutomationErrorHandler = None
         self._file_manager = FileManager()
         self._date_sequencer = DateSequencer()

         self._user_action_event = asyncio.Event() # Evento para esperar a ação do usuário do diálogo
         self._user_action = None # Armazena a ação escolhida pelo usuário ('continue', 'skip', 'abort')

         # Conecta o slot user_action_received a um método interno
         self.user_action_received.connect(self._handle_user_action_signal)


     def run_automation(self):
         """
         Este método é o ponto de entrada para a thread. Ele roda o loop asyncio.
         Chamado pelo sinal thread.started.
         """
         logger.info("Worker thread iniciada. Rodando loop asyncio...")
         try:
             asyncio.run(self._async_run())
         except Exception as e:
             logger.critical(f"Exceção fatal no loop asyncio do Worker: {e}", exc_info=True)
             self.finished.emit(f"Erro fatal: {e}")
         finally:
             logger.info("Worker thread finalizada.")
             # O sinal finished.emit já foi chamado

     async def _async_run(self):
         """Lógica principal assíncrona que inicia o navegador e a tarefa."""
         page = None
         try:
             headless = False # TODO: Fazer isso ser uma opção na GUI
             page = await self._browser_manager.launch_browser(headless=headless)

             # -- Inicializa o ErrorHandler com o callback --
             # O callback AGORA usará um método interno que EMITE UM SINAL para a GUI
             self._error_handler = AutomationErrorHandler(page, pause_callback=self._request_gui_action)

             # -- Carregar Dados e Configurações --
             main_date = self._file_manager.load_main_date_file()
             if not main_date:
                 raise AutomationError("Não foi possível carregar a data principal de data.csv")

             current_data_file = self._file_manager.find_next_file_to_process()

             # -- Loop de Processamento de Arquivos/Lotes --
             while current_data_file:
                 logger.info(f"Iniciando processamento do arquivo: {current_data_file.name}")

                 data_df = self._file_manager.load_data_file(current_data_file)
                 if data_df is None or data_df.empty:
                     logger.warning(f"Arquivo de dados vazio ou com erro: {current_data_file.name}. Pulando.")
                     self._file_manager.mark_file_as_processed(current_data_file)
                     current_data_file = self._file_manager.find_next_file_to_process()
                     continue

                 # -- Preparar e Rodar a Tarefa --
                 TaskClass = TASK_MAP.get(self._task_type)
                 if not TaskClass:
                     raise AutomationError(f"Tipo de tarefa desconhecido: {self._task_type}")

                 logger.info(f"Criando instância da tarefa: {TaskClass.__name__}")
                 task_instance = TaskClass(page, self._error_handler)

                 # -- Executar a Tarefa Principal --
                 # task_instance.run() irá rodar o loop pelos registros
                 # As exceções SkipRecordException e AbortAutomationException serão levantadas PELO HANDLER
                 # e capturadas DENTRO do _process_all_rows da BaseTask
                 # Se _process_all_rows for quebrado por AbortAutomationException,
                 # a exceção propagará para cá. SkipRecordException será tratada no loop interno da BaseTask.
                 try:
                     await task_instance.run()
                     # Se task_instance.run() terminar sem levantar AbortAutomationException,
                     # significa que todos os registros foram processados ou pulados via SkipRecordException
                     # (que é tratada dentro do loop da BaseTask).
                     logger.info(f"Tarefa principal para o arquivo {current_data_file.name} finalizada.")

                 except AbortAutomationException:
                     # Captura se a tarefa foi abortada pelo usuário
                     logger.error(f"Tarefa para o arquivo {current_data_file.name} abortada pelo usuário.")
                     # Não processa mais arquivos
                     break # Sai do loop de arquivos

                 # -- Marcar arquivo como processado e verificar o próximo --
                 # Este bloco SÓ é executado se a tarefa para o arquivo atual NÃO foi abortada
                 self._file_manager.mark_file_as_processed(current_data_file)
                 logger.info(f"Arquivo {current_data_file.name} marcado como processado.")

                 # Lógica para encontrar próximo arquivo e sua data correspondente
                 current_data_file = self._file_manager.find_next_file_to_process()
                 if current_data_file:
                     logger.info("Próximo arquivo na sequência encontrado.")
                     # Obter a próxima data da sequência para o NOVO arquivo
                     next_main_date = self._date_sequencer.get_next_sequence_date()
                     if next_main_date:
                          main_date = next_main_date # Atualiza a data para a próxima tarefa
                          logger.info(f"Usando a próxima data da sequência: {main_date}")
                     else:
                          logger.warning("Sequência de datas esgotada ou erro. Terminando loop de arquivos.")
                          break # Sai do loop de arquivos

             # -- Se o loop de arquivos terminou sem ser quebrado por AbortAutomationException --
             # Ou todos os arquivos foram processados, ou a sequência de datas/arquivos esgotou.
             logger.info("Loop principal de arquivos finalizado.")
             await self._browser_manager.close_browser()
             self.finished.emit("Sucesso") # Sinaliza sucesso


         except AutomationError as e:
             # Captura AutomationError que aconteceu ANTES ou DEPOIS do loop principal dos registros (ex: login)
             logger.error(f"Erro de automação fatal antes/depois do loop de registros: {e}")
             if page:
                  try: await page.close()
                  except: pass
             await self._browser_manager.close_browser()
             self.finished.emit(f"Falha na automação: {e.message}")

         except Exception as e:
             # Captura qualquer outra exceção inesperada e fatal
             logger.critical(f"Erro INESPERADO e fatal durante a automação: {e}", exc_info=True)
             if page:
                  try: await page.close()
                  except: pass
             await self._browser_manager.close_browser()
             self.finished.emit(f"Erro inesperado e fatal: {e}")


     # --- Métodos/Callbacks para comunicação bidirecional Worker <-> GUI ---

     async def _request_gui_action(self, error: AutomationError) -> str:
         """
         Callback chamado pelo AutomationErrorHandler na thread do Worker.
         Emite um sinal para a GUI principal e ESPERA a ação do usuário.
         Retorna a ação escolhida pelo usuário ('continue', 'skip', 'abort').
         """
         logger.info("Worker: Solicitando ação do usuário via GUI...")

         # Limpa o evento antes de emitir o sinal, para garantir que ele espere
         self._user_action_event.clear()
         self._user_action = None # Limpa a ação anterior

         # Emite o sinal para a thread principal da GUI exibir o diálogo de erro.
         # Como o slot que receberá este sinal (em MainWindow) exibirá um diálogo modal,
         # ele bloqueará a thread principal. Este método (que roda na thread do Worker)
         # precisa esperar a resposta da thread principal.
         # Esperamos no evento asyncio self._user_action_event.wait()
         self.request_error_dialog.emit(error) # Emite o sinal com o erro

         # Espera até que a thread principal tenha processado o diálogo e sinalizado
         # self._user_action_event.set() através do método self._handle_user_action_signal
         logger.debug("Worker: Esperando evento de ação do usuário...")
         # await self._user_action_event.wait() # Não pode usar await aqui, pois este callback é chamado POR UMA FUNÇÃO SÍNCRONA (do ErrorHandler)
         # SE o handler é chamado DENTRO de um método assíncrono da BasePage/Task,
         # o callback _request_gui_action É chamado de um contexto assíncrono.
         # Mas o handler em si (AutomationErrorHandler.handle_error) NÃO é async por padrão.
         # handle_error precisa ser async para poder await o callback.
         # Vamos ajustar o ErrorHandler para ser async. (Já fizemos isso no Passo 5).

         # Agora, como _request_gui_action é um callback de uma função async (_handler.handle_error),
         # podemos usar await self._user_action_event.wait() aqui.

         # CORREÇÃO: O callback para o ErrorHandler DEVE ser síncrono se o ErrorHandler não for async.
         # Mas o ErrorHandler PRECISA ser async para tirar screenshot e interagir com o evento asyncio.
         # Então, o ErrorHandler.handle_error é async. O callback fornecido a ele (_request_gui_action)
         # TAMBÉM será chamado em um contexto assíncrono (quando o handle_error for 'awaitado').
         # Portanto, _request_gui_action PODE ser async.

         # A questão é: O SINAL request_error_dialog.emit() é assíncrono? NÃO.
         # Emitir um sinal é síncrono. O slot que o recebe pode ser em outra thread.
         # O problema é ESPERAR o slot terminar.
         # QMetaObject.invokeMethod com Qt.BlockingQueuedConnection faz a espera BLOQUEANTE entre threads.
         # Mas não funciona bem com asyncio.
         # A melhor abordagem é a que já definimos:
         # 1. Handler (async) chama callback (async): `action = await self._request_gui_action(error)`
         # 2. Callback (`_request_gui_action` - async) EMITE SINAL para GUI: `self.request_error_dialog.emit(error)`
         # 3. Callback (continua): `await self._user_action_event.wait()` (ESPERA a resposta da GUI)
         # 4. MainWindow (GUI Thread) recebe SINAL, exibe diálogo.
         # 5. Usuário clica, diálogo fecha.
         # 6. MainWindow CHAMA MÉTODO no Worker (slot): `self.automation_worker.user_action_received.emit(user_action)`
         # 7. Worker recebe SINAL `user_action_received`, define `self._user_action` e `self._user_action_event.set()`.
         # 8. A espera `await self._user_action_event.wait()` no callback _request_gui_action termina.
         # 9. _request_gui_action retorna `self._user_action` para o Handler.

         # ENTÃO, o código abaixo para _request_gui_action está CORRETO para um callback async:
         await self._user_action_event.wait() # Espera a GUI processar o diálogo e sinalizar
         logger.debug("Worker: Evento de ação do usuário recebido.")
         return self._user_action # Retorna a ação para o Handler

     # --- Métodos/Slots chamados PELA THREAD PRINCIPAL DA GUI ---
     # Estes métodos recebem sinais da GUI (MainWindow)

     def _handle_user_action_signal(self, action: str):
         """
         Slot chamado pela MainWindow (GUI thread) após o usuário interagir com o diálogo de erro.
         Define a ação escolhida e sinaliza o evento asyncio para retomar o Worker.
         """
         logger.info(f"Worker: Recebido sinal de ação do usuário: {action}. Sinalizando evento asyncio.")
         self._user_action = action
         self._user_action_event.set() # Sinaliza para o await self._user_action_event.wait() no callback