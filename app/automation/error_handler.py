# Arquivo: app/automation/error_handler.py
import asyncio
from playwright.async_api import Page
from app.core.logger import logger
from app.core.errors import AutomationError # Importamos nossas exceções personalizadas
from pathlib import Path
import traceback # Para obter o stack trace do erro
from datetime import datetime # Importa datetime


class AutomationErrorHandler:
    """
    Gerencia erros durante a automação, permitindo pausar, continuar ou pular.
    """
    def __init__(self, page: Page, pause_callback=None):
        self._page = page # A instância da página Playwright
        self._is_paused = False
        self._pause_event = asyncio.Event() # Evento para pausar/retomar a execução asyncio
        self._pause_callback = pause_callback # Callback para notificar a GUI (fornecido pelo worker)
        self._last_error: AutomationError = None # Armazena o último erro capturado

        # Define um diretório para salvar screenshots de erros
        self._error_screenshots_dir = Path("error_screenshots")
        self._error_screenshots_dir.mkdir(parents=True, exist_ok=True) # Cria a pasta se não existir

    async def handle_error(self, e: Exception, step_description: str = "Passo desconhecido", data_row=None):
        """
        Processa um erro capturado, registra detalhes e entra em estado de pausa.
        Esta função é assíncrona porque pode precisar esperar por um evento de asyncio.
        """
        logger.error(f"Erro capturado durante o passo: '{step_description}'", exc_info=True) # exc_info=True printa o stack trace
        screenshot_path = None

        try:
            # Tenta tirar um screenshot
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_filename = f"error_{timestamp}.png"
            screenshot_path = self._error_screenshots_dir / screenshot_filename
            await self._page.screenshot(path=screenshot_path)
            logger.info(f"Screenshot de erro salvo em: {screenshot_path}")
        except Exception as screenshot_e:
            logger.error(f"Não foi possível tirar screenshot de erro: {screenshot_e}")
            screenshot_path = "Não disponível" # Marca como não disponível

        # Cria a exceção personalizada com os detalhes do erro
        # Incluímos o stack trace original na mensagem para melhor depuração
        error_message = f"{e}\nOriginal Stack Trace:\n{traceback.format_exc()}"
        self._last_error = AutomationError(
            message=error_message,
            step=step_description,
            data=data_row,
            screenshot_path=str(screenshot_path) if screenshot_path != "Não disponível" else None
        )

        self._is_paused = True
        logger.warning("Automação pausada devido ao erro.")

        # Notifica a GUI sobre o erro e a pausa
        if self._pause_callback:
             # Chamamos o callback. A GUI (Worker) deve esperar pela resposta do usuário.
             # O callback deve retornar a ação desejada (continue, skip, abort)
             action = await self._pause_callback(self._last_error)
             logger.info(f"GUI solicitou ação: {action}")

             if action == "continue":
                 self._is_paused = False # Remove o estado de pausa
                 self._pause_event.set() # Sinaliza para continuar
             elif action == "skip":
                 self._is_paused = False # Remove o estado de pausa
                 self._pause_event.set() # Sinaliza para continuar (o TaskRunner lidará com o 'skip')
                 # Poderíamos levantar uma exceção específica aqui para o TaskRunner pegar
                 raise SkipRecordException("Solicitado pular registro pelo usuário.") # Usaremos uma nova exceção
             elif action == "abort":
                 self._is_paused = False # Remove o estado de pausa
                 self._pause_event.set() # Sinaliza para continuar (o TaskRunner lidará com o 'abort')
                 # Poderíamos levantar uma exceção específica aqui
                 raise AbortAutomationException("Automação abortada pelo usuário.") # Usaremos uma nova exceção
             else:
                 logger.error(f"Ação desconhecida recebida do callback: {action}. Abortando.")
                 raise AbortAutomationException("Ação de controle desconhecida.")


        # Se não houver callback, o robô fica pausado até que alguém chame resume() externamente
        # await self._pause_event.wait() # Espera até que o evento seja setado externamente (menos ideal para integração GUI)


    def resume(self):
        """Retoma a execução da automação (chamado pela GUI/Worker)."""
        if self._is_paused:
            self._is_paused = False
            self._last_error = None # Limpa o último erro
            self._pause_event.set() # Sinaliza para continuar
            self._pause_event.clear() # Limpa o evento para a próxima pausa
            logger.info("Automação retomada.")
        else:
            logger.warning("Tentativa de retomar automação que não estava pausada.")

    def skip_record(self):
        """Sinaliza para pular o registro atual (chamado pela GUI/Worker)."""
        if self._is_paused:
             self._is_paused = False
             self._last_error = None
             self._pause_event.set() # Sinaliza para continuar
             self._pause_event.clear()
             logger.info("Solicitado pular registro.")
             # O TaskRunner precisa capturar isso. Poderíamos usar uma exceção interna ou estado.
             # Uma exceção é mais limpa para interromper a lógica atual.
             raise SkipRecordException("Pular registro solicitado.") # Levanta uma exceção interna

        else:
             logger.warning("Tentativa de pular registro em automação que não estava pausada.")


    def abort(self):
        """Sinaliza para abortar a automação (chamado pela GUI/Worker)."""
        if self._is_paused:
            self._is_paused = False
            self._last_error = None
            self._pause_event.set() # Sinaliza para continuar
            self._pause_event.clear()
            logger.info("Automação abortada.")
            # O TaskRunner precisa capturar isso.
            raise AbortAutomationException("Automação abortada pelo usuário.") # Levanta uma exceção interna
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