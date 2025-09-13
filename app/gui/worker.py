# Arquivo: app/gui/worker.py - Version: 1c - Passa info UBS/User para ErrorDialo

from PyQt5.QtCore import QObject, pyqtSignal, QThread
from PyQt5.QtWidgets import QApplication
import asyncio
from app.automation.browser import BrowserManager
from app.automation.error_handler import AutomationErrorHandler, AbortAutomationException
# Importe as classes das suas Tarefas específicas aqui
from app.automation.tasks.atend_hipertenso_task import AtendimentoHipertensoTask
from app.automation.tasks.atend_diabetico_task import AtendimentoDiabeticoTask
# from app.automation.tasks.atend_a97_task import AtendimentoA97Task # Se necessário
from app.automation.tasks.atend_saude_mamografia_task import AtendimentoMamografiaTask
from app.automation.tasks.proce_afericao_task import ProcedimentoAfericaoTask
from app.automation.tasks.proce_saude_repro_task import ProcedimentoSaudeReproTask
from app.automation.tasks.atend_saude_repro_task import AtendimentoSaudeReproTask
# from app.automation.tasks.hipertenso_procedimento_task import HipertensoProcedimentoTask
from app.automation.tasks.proce_diabetes_task import ProcedimentoDiabeticoTask

# Importe ACS - ATD - HIPERTENSO Task
from app.automation.tasks.acs_atd_hipertenso_task import AcsAtdHipertensoTask


from app.core.logger import logger
from app.core.errors import AutomationError

# Define um dicionário para mapear o tipo de tarefa selecionado na GUI
# para a classe da tarefa correspondente
TASK_MAP = {
    "Atend. Hipertenso": AtendimentoHipertensoTask,
    "Proc. Hipertenso": ProcedimentoAfericaoTask,
    "ACS - ATD - HIPERTENSO": AcsAtdHipertensoTask, 
    "Atend. Diabetico": AtendimentoDiabeticoTask,
    "Proc. Diabéticos": ProcedimentoDiabeticoTask,
    "ATD - Mamografia": AtendimentoMamografiaTask,
    "Atend. Saúde/Reprod.": AtendimentoSaudeReproTask,
    "Proc. Saúde/Reprod.": ProcedimentoSaudeReproTask,
    
    # "Hipertenso e Procedimento": HipertensoProcedimentoTask,
    # "Atendimento SEM DOENÇA": AtendimentoA97Task,
    # Adicione outras tarefas aqui
}


class Worker(QObject):
    """
    Objeto que roda a lógica assíncrona da automação dentro de uma QThread.
    Usa sinais para se comunicar com a GUI principal.
    """
    finished = pyqtSignal(str)
    request_error_dialog = pyqtSignal(object, dict)
    # user_action_received = pyqtSignal(str)

    def __init__(self, task_type: str, manual_login: bool, use_chrome_browser: bool):
        super().__init__(None)
        self._task_type = task_type
        self._manual_login = manual_login
        self._use_chrome_browser = use_chrome_browser
        self._browser_manager = BrowserManager()
        self._error_handler: AutomationErrorHandler = None
        self._user_action_event = asyncio.Event()
        self._user_action = None
        # self.user_action_received.connect(self._handle_user_action_signal)
        logger.debug(f"Worker initialized for task '{task_type}'. user_action_received signal connected in Worker. Using Chrome: {use_chrome_browser}")
    
    # Este método agora é o SLOT direto para MainWindow.user_action_signal
    def _handle_user_action_signal(self, action: str):
        """
        Slot que recebe a ação do usuário da GUI e libera o worker.
        """
        logger.info(f"Worker {id(self)}: Recebido sinal de ação do usuário no slot: {action}.")
        self._user_action = action
        self._user_action_event.set()
        logger.debug(f"Worker {id(self)}: _user_action_event set for action '{action}'.")

    def run_automation(self):
        """
        Ponto de entrada para a thread. Roda o loop asyncio.
        """
        logger.info("Worker thread iniciada. Rodando loop asyncio...")
        try:
            # É uma boa prática criar um novo loop de eventos para a QThread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._async_run())
            loop.close()
        except Exception as e:
            logger.critical(f"Exceção fatal no loop asyncio do Worker: {e}", exc_info=True)
            self.finished.emit(f"Erro fatal: {e}")
        finally:
            logger.info("Worker thread finalizada.")

    async def _async_run(self):
        """Lógica principal assíncrona que inicia o navegador e a tarefa."""
        page = None
        try:
            headless = False
            page = await self._browser_manager.launch_browser(headless=headless, use_chrome=self._use_chrome_browser)
            self._error_handler = AutomationErrorHandler(page, pause_callback=self._request_gui_action)

            # --- CORREÇÃO: A lógica de loop de arquivos foi removida daqui ---
            # A MainWindow já verificou se há arquivos, e a BaseTask gerenciará todo o fluxo.

            TaskClass = TASK_MAP.get(self._task_type)
            if not TaskClass:
                raise AutomationError(f"Tipo de tarefa desconhecido: {self._task_type}")

            logger.info(f"Criando instância da tarefa: {TaskClass.__name__}")
            task_instance = TaskClass(page, self._error_handler, manual_login=self._manual_login)

            # Executa a tarefa principal. O método .run() da BaseTask agora contém
            # toda a lógica: login, navegação, loop de arquivos e loop de registros.
            await task_instance.run()

            # Se task_instance.run() terminar sem exceções, a automação foi bem-sucedida.
            logger.info("Tarefa de automação concluída com sucesso.")
            await self._browser_manager.close_browser()
            self.finished.emit("Sucesso")

        except AbortAutomationException as e:
            logger.warning(f"Automação interrompida pelo usuário: {e}")
            if page:
                try: await page.close()
                except: pass
            await self._browser_manager.close_browser()
            self.finished.emit(f"Terminada pelo usuário")

        except AutomationError as e:
            logger.error(f"Erro de automação fatal: {e}")
            if page:
                try: await page.close()
                except: pass
            await self._browser_manager.close_browser()
            self.finished.emit(f"Falha na automação: {e.message}")

        except Exception as e:
            logger.critical(f"Erro INESPERADO e fatal durante a automação: {e}", exc_info=True)
            if page:
                try: await page.close()
                except: pass
            await self._browser_manager.close_browser()
            self.finished.emit(f"Erro inesperado e fatal: {e}")


    async def _request_gui_action(self, error: AutomationError, user_info: dict = None) -> str:
        """
        Callback chamado pelo ErrorHandler. Emite um sinal para a GUI e espera a resposta.
        """
        logger.info("Worker: Solicitando ação do usuário via GUI...")
        self._user_action_event.clear()
        self._user_action = None
        self.request_error_dialog.emit(error, user_info)
        logger.debug("Worker: _request_gui_action emitted request_error_dialog. Waiting for user action event...")

        # --- INÍCIO DA MODIFICAÇÃO CRÍTICA PARA PROCESSAR EVENTOS QT ---
        # Enquanto o evento não for setado, processa eventos da Qt na thread do Worker
        while not self._user_action_event.is_set():
            app = QApplication.instance()
            if app:
                # Processa eventos do aplicativo principal. Isso pode incluir sinais
                # direcionados a objetos nesta thread worker.
                app.processEvents() 
            else:
                logger.error("QApplication instance not found in worker thread. Cannot process Qt events.")
                # Se não há QApplication, não há como processar sinais Qt.
                # Não podemos esperar aqui indefinidamente. Uma saída forçada pode ser necessária.
                # Por enquanto, vamos apenas logar e dormir para evitar loop infinito de CPU.
            
            await asyncio.sleep(0.05) # Pequena pausa para não consumir CPU em excesso

        logger.debug(f"Worker: _request_gui_action received user action event. Action: {self._user_action}")
        return self._user_action

    