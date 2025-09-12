# Arquivo: app/automation/error_handler.py
import asyncio
from playwright.async_api import Page
from app.core.logger import logger
from app.core.errors import AutomationError # Importamos nossas exceções personalizadas
from pathlib import Path
import traceback # Para obter o stack trace do erro
from datetime import datetime # Importa datetime
from playwright._impl._errors import TargetClosedError


class AutomationErrorHandler:
    """
    Gerencia erros durante a automação, permitindo pausar, continuar ou pular.
    """
    def __init__(self, page: Page, pause_callback=None):
        super().__init__() # Adicionado super().__init__() para QObject base, embora aqui não seja QObject.
        self._page = page # A instância da página Playwright
        self._is_paused = False
        self._pause_event = asyncio.Event() # Evento para pausar/retomar a execução asyncio
        self._pause_callback = pause_callback # Callback para notificar a GUI (fornecido pelo worker)
        self._last_error: AutomationError = None # Armazena o último erro capturado

        # Define um diretório para salvar screenshots de erros
        self._error_screenshots_dir = Path("error_screenshots")
        self._error_screenshots_dir.mkdir(parents=True, exist_ok=True) # Cria a pasta se não existir

    async def handle_error(self, e: Exception, step_description: str = "Passo desconhecido", data_row=None) -> str:
        logger.error(f"Erro capturado durante o passo: '{step_description}'", exc_info=True)
        screenshot_path = None
        
        # --- INÍCIO DA MODIFICAÇÃO PARA CHECAR `TargetClosedError` ---
        is_page_closed = False
        # Verifique se a exceção original já é um TargetClosedError
        if isinstance(e, TargetClosedError):
            is_page_closed = True
            logger.warning(f"Erro original é TargetClosedError. A página já está fechada.")
        elif self._page and self._page.is_closed(): # Verifica se a página já está marcada como fechada
            is_page_closed = True
            logger.warning("Page.is_closed() retornou True. A página está fechada.")
        
        try:
            if not is_page_closed: # Tente tirar screenshot apenas se a página não estiver fechada
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_filename = f"error_{timestamp}.png"
                screenshot_path = self._error_screenshots_dir / screenshot_filename
                await self._page.screenshot(path=screenshot_path)
                logger.info(f"Screenshot de erro salvo em: {screenshot_path}")
        except TargetClosedError as screenshot_e:
            is_page_closed = True # Confirma que foi fechado durante a tentativa de screenshot
            logger.error(f"Não foi possível tirar screenshot de erro: Page/Context já fechado ({screenshot_e})")
            screenshot_path = "Não disponível (Target Closed)"
        except Exception as screenshot_e:
            logger.error(f"Não foi possível tirar screenshot de erro: {screenshot_e}", exc_info=True)
            screenshot_path = "Não disponível"
        # --- FIM DA MODIFICAÇÃO PARA CHECAR `TargetClosedError` ---

        # Cria a exceção personalizada com os detalhes do erro
        error_message = f"{e}\nOriginal Stack Trace:\n{traceback.format_exc()}"
        self._last_error = AutomationError(
            message=error_message,
            step=step_description,
            data=data_row,
            screenshot_path=str(screenshot_path) if screenshot_path != "Não disponível" else None
        )

        self._is_paused = True
        logger.warning("Automação pausada devido ao erro.")

        action = "abort" # Ação padrão
        # Se a página está fechada, não há como continuar, força abortar.
        if is_page_closed:
            logger.critical("Browser/Page está fechado. Forçando ABORTAR Automação, pois não é possível continuar.")
            action = "abort"
        else:
            if self._pause_callback:
                 action = await self._pause_callback(self._last_error)
                 logger.info(f"GUI solicitou ação: {action}")

        # Com base na ação do usuário, ou levantamos uma exceção de controle ou retornamos "continue"
        if action == "continue":
            self._is_paused = False # Remove o estado de pausa
            self._pause_event.set() # Sinaliza para continuar
            return "continue" # Retorna explicitamente "continue"
        elif action == "skip":
            self._is_paused = False # Remove o estado de pausa
            self._pause_event.set() # Sinaliza para continuar (o TaskRunner lidará com o 'skip')
            raise SkipRecordException("Solicitado pular registro pelo usuário.")
        elif action == "abort":
            self._is_paused = False # Remove o estado de pausa
            self._pause_event.set() # Sinaliza para continuar (o TaskRunner lidará com o 'abort')
            raise AbortAutomationException("Automação abortada pelo usuário.")
        else:
            logger.error(f"Ação desconhecida recebida do callback: {action}. Abortando.")
            raise AbortAutomationException("Ação de controle desconhecida.")

    # Os métodos `resume`, `skip_record` e `abort` permanecem inalterados.
    def resume(self):
        if self._is_paused:
            self._is_paused = False
            self._last_error = None
            self._pause_event.set()
            self._pause_event.clear()
            logger.info("Automação retomada.")
        else:
            logger.warning("Tentativa de retomar automação que não estava pausada.")

    def skip_record(self):
        if self._is_paused:
             self._is_paused = False
             self._last_error = None
             self._pause_event.set()
             self._pause_event.clear()
             logger.info("Solicitado pular registro.")
             raise SkipRecordException("Pular registro solicitado.")
        else:
             logger.warning("Tentativa de pular registro em automação que não estava pausada.")

    def abort(self):
        if self._is_paused:
            self._is_paused = False
            self._last_error = None
            self._pause_event.set()
            self._pause_event.clear()
            logger.info("Automação abortada.")
            raise AbortAutomationException("Automação abortada pelo usuário.")
        else:
            logger.warning("Tentativa de abortar automação que não estava pausada.")



    @property
    def is_paused(self):
        return self._is_paused

    @property
    def last_error(self):
        return self._last_error

# Definimos exceções internas para controle de fluxo do ErrorHandler para o TaskRunner
class SkipRecordException(Exception):
    """Exceção interna para sinalizar que o registro atual deve ser pulado."""
    pass

class AbortAutomationException(Exception):
    """Exceção interna para sinalizar que a automação deve ser abortada."""
    pass


# Exemplo de uso (somente para teste do módulo - simula um erro e o callback da GUI)
if __name__ == '__main__':
    # Mock de uma página Playwright e um callback da GUI
    class MockPage:
         async def screenshot(self, path):
              print(f"MockPage: Salvando screenshot em {path}")
         @property
         def url(self):
              return "mock://test.com"

    def mock_gui_callback(error_details: AutomationError):
        print("\n" + "="*30)
        print("=== ROBÔ PAUSADO ===")
        print(error_details)
        print("==="*10)
        # Simula a interação do usuário
        action = input("Ação (continue/skip/abort): ").strip().lower()
        while action not in ["continue", "skip", "abort"]:
             action = input("Ação inválida. Digite continue, skip ou abort: ").strip().lower()
        print(f"Callback simulado retornando: {action}")
        print("="*30 + "\n")
        return action # Retorna a ação escolhida pelo "usuário"

    async def test_error_handling():
        mock_page = MockPage()
        handler = AutomationErrorHandler(mock_page, pause_callback=mock_gui_callback)

        print("Simulando uma operação que falha...")
        step = "Clicar botão 'Confirmar'"
        data = ["manha", "12345678900", "01/01/1990", 1, "UBS Teste", "Inicial", "Hipertensao", "Alta"] # Dados de exemplo
        try:
            # Simula que um erro de elemento não encontrado aconteceu
            raise Exception("Elemento não encontrado usando o seletor X") # Ou ElementNotFoundError real
            # Em um cenário real, isso seria capturado dentro de um método de 'Page' ou 'Task'
        except Exception as e:
            # Aqui, o ErrorHandler entra em ação
            try:
                 await handler.handle_error(e, step, data)

                 # Após o handle_error, se a ação foi 'continue' ou 'skip', a execução continua aqui
                 if not handler.is_paused:
                     print("Handler processou o erro e a automação foi sinalizada para continuar/pular.")
                 else:
                     print("Handler processou o erro e a automação ainda está pausada (callback não retomou?).") # Não deve acontecer com o callback

            except SkipRecordException:
                 print("Exceção interna SkipRecordException capturada no ponto de chamada do handler.")
                 # Aqui o TaskRunner real pularia para a próxima linha
            except AbortAutomationException:
                 print("Exceção interna AbortAutomationException capturada no ponto de chamada do handler.")
                 # Aqui o TaskRunner real abortaria tudo

        print("\nSimulação finalizada.")


    asyncio.run(test_error_handling())