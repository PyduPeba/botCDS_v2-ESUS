# Arquivo: app/gui/worker.py
from PyQt5.QtCore import QObject, pyqtSignal
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
    request_error_dialog = pyqtSignal(object)
    user_action_received = pyqtSignal(str)

    def __init__(self, task_type: str, manual_login: bool):
        super().__init__(None)
        self._task_type = task_type
        self._manual_login = manual_login
        self._browser_manager = BrowserManager()
        self._error_handler: AutomationErrorHandler = None
        self._user_action_event = asyncio.Event()
        self._user_action = None
        self.user_action_received.connect(self._handle_user_action_signal)

    def run_automation(self):
        """
        Ponto de entrada para a thread. Roda o loop asyncio.
        """
        logger.info("Worker thread iniciada. Rodando loop asyncio...")
        try:
            asyncio.run(self._async_run())
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
            page = await self._browser_manager.launch_browser(headless=headless)

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

    async def _request_gui_action(self, error: AutomationError) -> str:
        """
        Callback chamado pelo ErrorHandler. Emite um sinal para a GUI e espera a resposta.
        """
        logger.info("Worker: Solicitando ação do usuário via GUI...")
        self._user_action_event.clear()
        self._user_action = None
        self.request_error_dialog.emit(error)
        await self._user_action_event.wait()
        logger.debug(f"Worker: Evento de ação do usuário recebido: {self._user_action}")
        return self._user_action

    def _handle_user_action_signal(self, action: str):
        """
        Slot que recebe a ação do usuário da GUI e libera o worker.
        """
        logger.info(f"Worker: Recebido sinal de ação do usuário: {action}.")
        self._user_action = action
        self._user_action_event.set()