# Arquivo: app/automation/pages/base_page.py (CORRIGIDO 64)
from playwright.async_api import Page, Locator
from app.core.logger import logger
from app.core.errors import ElementNotFoundError, ElementNotInteractableError, AutomationError
from app.automation.error_handler import AutomationErrorHandler # Importamos o handler
import asyncio # Importamos asyncio para await sleeps controlados
from playwright._impl._errors import TimeoutError # Importa TimeoutError

class BasePage:
    """
    Classe base para representar uma página ou componente no e-SUS.
    Contém métodos de interação comuns e integração com o ErrorHandler.
    """
    def __init__(self, page: Page, error_handler: AutomationErrorHandler):
        self._page = page # A instância da página Playwright
        self._handler = error_handler # A instância do gerenciador de erros
    
    # ** ATRIBUTOS E MÉTODOS PARA MÁSCARA DE CARREGAMENTO E POPUPS **
    _LOADING_MASK_SELECTOR = 'div.ext-el-mask' # Seletor para a máscara de carregamento ExtJS
    _MESSAGE_BOX_POPUP_SELECTOR = 'div[peid="message-box"]' # Seletor padrão para o popup message-box
    _MESSAGE_BOX_OK_BUTTON_SELECTOR = f'{_MESSAGE_BOX_POPUP_SELECTOR} button:has-text("OK")' # Botão OK

    async def _wait_for_loading_mask_to_disappear(self, timeout=5000):
        """
        Espera a máscara de carregamento (div.ext-el-mask) desaparecer.
        Se a máscara não sumir, aciona o handler manual.
        """
        mask_locator = self._page.locator(self._LOADING_MASK_SELECTOR)
        try:
            logger.debug(f"Esperando a máscara de carregamento desaparecer (Selector: {mask_locator.locator})...")
            await mask_locator.wait_for(state="hidden", timeout=timeout)
            logger.debug("Máscara de carregamento desapareceu.")
        except TimeoutError:
            logger.warning("Timeout esperando a máscara de carregamento desaparecer.")
            # Chamamos o handler com um erro sobre a máscara.
            # O handler pausará. Se o usuário continuar, o _safe_... tentará o clique mesmo assim.
            await self._handler.handle_error(TimeoutError("Máscara de carregamento não desapareceu."),
                                              step_description="Esperando máscara de carregamento sumir")
        except Exception as e:
            logger.error(f"Erro inesperado ao esperar máscara de carregamento: {e}", exc_info=True)
            user_action = await self._handler.handle_error(e, step_description="Erro inesperado esperando máscara de carregamento")
            if user_action == "continue":
                logger.info("Usuário optou por continuar apesar do erro na máscara de carregamento.")
            raise AutomationError("Retentando registro devido à máscara de carregamento após intervenção manual.") from e

    async def _safe_click(self, locator: Locator, step_description: str):
     """Clica em um elemento com tratamento de erro."""
     # ** CORREÇÃO: Use apenas locator.locator no log síncrono **
     logger.debug(f"Tentando clicar no elemento: {step_description} (Selector: {locator.locator})")
     try:
         await locator.wait_for(state="visible", timeout=10000)
         await locator.click()
         logger.debug(f"Clicado com sucesso em: {step_description}")
     except Exception as e:
         await self._handler.handle_error(e, step_description=f"Clicar: {step_description}")
        #  raise e # Re-levanta a exceção original

    async def _safe_fill(self, locator: Locator, text: str, step_description: str):
     """Preenche um campo de texto com tratamento de erro."""
     # ** CORREÇÃO: Use apenas locator.locator no log síncrono **
     logger.debug(f"Tentando preencher campo: '{step_description}' com texto: '{text}' (Selector: {locator.locator})")
     try:
         await locator.wait_for(state="visible", timeout=10000)
         await locator.fill(text)
         logger.debug(f"Campo '{step_description}' preenchido com sucesso.")
     except Exception as e:
            user_action = await self._handler.handle_error(e, step_description=f"Preencher: {step_description}", data_row={"text_to_fill": text})
            if user_action == "continue":
                raise AutomationError(f"Retentando registro devido ao preenchimento de '{step_description}' após intervenção manual.") from e
    
    async def _safe_fill_simule(self, locator: Locator, text: str, step_description: str, delay_ms: int = 20): #Padrão 100ms testado
        """
        Simula digitação realista em um campo de texto, usando `.type()` com delay entre teclas.
        Útil para campos que disparam eventos como autocomplete apenas com interação humana.
        """
        logger.debug(f"Tentando simular preenchimento do campo: '{step_description}' com texto: '{text}' (Selector: {locator.locator})")
        try:
            # Aguarda o campo estar visível
            await locator.wait_for(state="visible", timeout=10000)

            # Clica no campo para focar
            await locator.click()
            await asyncio.sleep(0.1)

            # Limpa o campo antes de digitar
            await locator.fill("")  # Opcional: use select_all + Backspace se necessário

            # Digita simulando usuário real
            await locator.type(text, delay=delay_ms)
            await asyncio.sleep(0.1) # Pequena pausa após digitar

            logger.debug(f"Campo '{step_description}' preenchido com sucesso usando digitação simulada.")

        except Exception as e:
            user_action = await self._handler.handle_error(e, step_description=f"Preencher (simulado): {step_description}", data_row={"text_to_fill": text})
            if user_action == "continue":
                raise AutomationError(f"Retentando registro devido ao preenchimento simulado de '{step_description}' após intervenção manual.") from e


    async def _safe_select_option(self, locator: Locator, value: str, step_description: str):
         """Seleciona uma opção em um dropdown (seletor <select>) com tratamento de erro."""
         logger.debug(f"Tentando selecionar '{value}' no dropdown: '{step_description}' (Selector: {locator.all_text_contents() or locator.locator})")
         try:
             await locator.wait_for(state="visible", timeout=10000)
             await locator.select_option(value)
             logger.debug(f"Opção '{value}' selecionada com sucesso no dropdown '{step_description}'.")
         except Exception as e:
            user_action = await self._handler.handle_error(e, step_description=f"Selecionar opção '{value}' no dropdown: {step_description}", data_row={"value_to_select": value})
            if user_action == "continue":
                raise AutomationError(f"Retentando registro devido à seleção de opção em '{step_description}' após intervenção manual.") from e

    async def _safe_wait_for_selector(self, selector: str, state="visible", timeout=10000, step_description: str = None):
        """Espera por um seletor com tratamento de erro."""
        desc = step_description if step_description else f"Esperar por seletor: {selector}"
        logger.debug(f"Tentando esperar por: {desc}")
        try:
            await self._page.wait_for_selector(selector, state=state, timeout=timeout)
            logger.debug(f"Seletor encontrado: {desc}")
            return self._page.locator(selector) # Retorna o locator para uso posterior
        except Exception as e:
            await self._handler.handle_error(e, step_description=f"Esperar por: {desc}")
            # Re-levantar implicitamente
            # Note: Se handle_error levantar Skip/Abort, este ponto não será alcançado.
            # Se ele apenas retornar, a exceção original (e) será re-levantada.
            # O chamador precisará estar preparado para capturar e/ou deixar propagar.
            # Uma alternativa seria o handle_error levantar SEMPRE AutomationError,
            # e o TaskRunner capturar apenas AutomationError, SkipRecordException, AbortAutomationException.
            # Vamos seguir com a segunda abordagem: handle_error levanta suas exceções de controle.

    async def _safe_goto(self, url: str, step_description: str = "Navegar para URL"):
         """Navega para uma URL com tratamento de erro."""
         logger.debug(f"Tentando navegar para: {url}")
         try:
              await self._page.goto(url, wait_until="domcontentloaded", timeout=30000) # Espera 30s pela URL
              logger.info(f"Navegado com sucesso para: {url}")
         except Exception as e:
              await self._handler.handle_error(e, step_description=f"Navegar para: {step_description}")
              # Re-levantar implicitamente

    async def _safe_press(self, locator: Locator, key: str, step_description: str):
        """Pressiona uma tecla em um elemento com tratamento de erro."""
        logger.debug(f"Tentando pressionar tecla '{key}' no elemento: '{step_description}'")
        try:
             await locator.wait_for(state="visible", timeout=10000)
             await locator.press(key)
             logger.debug(f"Tecla '{key}' pressionada com sucesso em '{step_description}'.")
        except Exception as e:
             await self._handler.handle_error(e, step_description=f"Pressionar tecla '{key}': {step_description}")
             # Re-levantar implicitamente

    async def _safe_type_with_delay(self, locator: Locator, text: str, delay_ms: int = 100, step_description: str = "Preencher campo com delay"):
        """Preenche um campo de texto digitando caractere por caractere com delay."""
        logger.debug(f"Tentando digitar em: '{step_description}' com texto: '{text}' (Delay: {delay_ms}ms)")
        try:
            await locator.wait_for(state="visible", timeout=10000)
            await locator.wait_for(state="enabled", timeout=5000)
            await locator.type(text, delay=delay_ms) # Usa page.type com delay
            logger.debug(f"Digitação em '{step_description}' completa.")
        except Exception as e:
            await self._handler.handle_error(e, step_description=f"Digitar com delay: {step_description}", data_row={"text_to_fill": text})


    async def _safe_click_by_text(self, text: str, step_description: str = "Clicar por texto"):
        """Procura e clica em um elemento pelo seu texto visível com tratamento de erro."""
        # Cria um locator que procura qualquer elemento com o texto especificado
        locator = self._page.locator(f"text='{text}'")
        logger.debug(f"Tentando clicar no elemento com texto: '{text}' ({step_description})")
        await self._safe_click(locator, step_description=f"Clicar texto: '{text}' ({step_description})")


    # --- Métodos para interagir com IFrames ---
    async def _safe_switch_to_iframe(self, iframe_selector: str, step_description: str = "Mudar para Iframe"):
        """Espera por um iframe e muda o contexto da página para ele."""
        logger.debug(f"Tentando mudar para iframe: {iframe_selector}")
        try:
            # Espera pelo iframe estar presente e visível
            iframe_locator = self._page.locator(iframe_selector)
            await iframe_locator.wait_for(state="visible", timeout=20000) # Espera mais tempo para iframe
            
            # Retorna a instância do frame
            frame = self._page.frame_locator(iframe_selector)
            if not frame:
                 raise ElementNotFoundError(f"Iframe encontrado mas não foi possível obter a instância do frame com seletor: {iframe_selector}")

            logger.info(f"Contexto mudado para iframe: {iframe_selector}")
            return frame # Retorna a instância FrameLocator
        except Exception as e:
            await self._handler.handle_error(e, step_description=f"Mudar para iframe: {step_description}")
            # Re-levantar implicitamente

    async def _safe_switch_to_default_content(self):
        """Muda o contexto de volta para o conteúdo principal da página."""
        logger.debug("Tentando mudar para conteúdo principal.")
        try:
             # Não há um método direto 'switch_to_default_content' como no Selenium.
             # A instância 'page' sempre refere-se ao frame principal por padrão.
             # Após trabalhar em um frame, basta usar métodos em 'self._page' novamente.
             # No entanto, para simular a intenção e ter um log/handler entry:
             logger.info("Contexto retornado para o conteúdo principal (usando instância page).")
             # Não há uma operação assíncrona aqui, mas mantemos a estrutura async para consistência.
             pass # Não faz nada assíncrono, mas representa o ponto de retorno lógico
        except Exception as e:
            # Isso provavelmente não acontecerá a menos que haja um problema inesperado com o logger ou handler
            await self._handler.handle_error(e, step_description="Mudar para conteúdo principal")
            # Re-levantar implicitamente
    
    

    async def _handle_ciap_alert(self, page_or_frame: Page | Locator) -> str:
        """
        Lida com popups de alerta padrão (message-box) que podem aparecer após certas interações.
        Retorna "handled" se o popup foi detectado e o OK clicado, "not_detected" caso contrário, "error" se houve falha no tratamento.
        """
        logger.debug("Verificando por popup de alerta padrão (message-box)...")
        popup_locator = page_or_frame.locator(self._MESSAGE_BOX_POPUP_SELECTOR)

        try:
            # Espera um curto período pelo popup. Se aparecer, o try tem sucesso.
            await popup_locator.wait_for(state="visible", timeout=2000)
            logger.warning("Popup de alerta padrão (message-box) detectado. Clicando em 'OK'.")

            ok_button_locator = page_or_frame.locator(self._MESSAGE_BOX_OK_BUTTON_SELECTOR)
            await self._safe_click(ok_button_locator, step_description="Botão 'OK' no popup message-box")
            logger.debug("Botão 'OK' do popup message-box clicado.")
            await popup_locator.wait_for(state="hidden", timeout=2000)
            logger.debug("Popup message-box fechado.")
            return "handled"

        except TimeoutError:
            logger.debug("Popup de alerta padrão (message-box) NÃO detectado.")
            return "not_detected"
        except Exception as e:
            logger.error(f"Erro inesperado ao tentar tratar popup de alerta padrão: {e}", exc_info=True)
            # Não levanta exceção aqui, pois já estamos dentro de um handler ou chamando como utilitário.
            return "error" # Sinaliza que houve um erro no tratamento.


# # Exemplo de uso (para teste do módulo - precisa de um mock de Page e ErrorHandler)
# # if __name__ == '__main__':
#     class MockLocator:
#          def __init__(self, text=None, selector="mock_selector"):
#               self._text = text
#               self._selector = selector

#          async def wait_for(self, state="visible", timeout=10000):
#               print(f"  MockLocator: Esperando por estado '{state}' no seletor '{self._selector}'...")
#               if self._selector == "fail_selector":
#                    await asyncio.sleep(0.1) # Simula uma pequena espera antes de falhar
#                    raise TimeoutError(f"Mock timeout para {self._selector}")
#               print(f"  MockLocator: Estado '{state}' encontrado.")

#          async def click(self):
#               print(f"  MockLocator: Clicando no seletor '{self._selector}'...")
#               if "uninteractable" in self._selector:
#                    raise Exception(f"Mock: Elemento não interativo '{self._selector}'") # Simula ElementNotInteractableError
#               print(f"  MockLocator: Clique bem-sucedido.")

#          async def fill(self, text):
#               print(f"  MockLocator: Preenchendo seletor '{self._selector}' com '{text}'...")
#               print(f"  MockLocator: Preenchimento bem-sucedido.")

#          async def select_option(self, value):
#               print(f"  MockLocator: Selecionando opção '{value}' no seletor '{self._selector}'...")
#               print(f"  MockLocator: Seleção bem-sucedida.")

#          async def press(self, key):
#              print(f"  MockLocator: Pressionando tecla '{key}' no seletor '{self._selector}'...")
#              print(f"  MockLocator: Tecla pressionada com sucesso.")

#          async def type(self, text, delay=100):
#              print(f"  MockLocator: Digitanto texto '{text}' com delay {delay}ms no seletor '{self._selector}'...")
#              print(f"  MockLocator: Digitação completa.")

#          def all_text_contents(self):
#               return [self._text] if self._text else []
#          @property
#          def locator(self):
#               return self._selector


#     class MockPage:
#         def __init__(self):
#             self._locators = {} # Dicionário para simular localizadores

#         def locator(self, selector):
#              if selector in self._locators:
#                   return self._locators[selector]
#              # Cria um locator mock se não existir, para simular sucesso por padrão
#              new_locator = MockLocator(selector=selector)
#              self._locators[selector] = new_locator
#              return new_locator

#         async def wait_for_selector(self, selector, state="visible", timeout=10000):
#             print(f"MockPage: Esperando por seletor '{selector}'...")
#             if selector == "fail_wait_selector":
#                 await asyncio.sleep(0.1) # Simula pequena espera antes de falhar
#                 raise TimeoutError(f"Mock timeout para wait_for_selector: {selector}")
#             print(f"MockPage: Seletor '{selector}' encontrado.")
#             return self.locator(selector) # Retorna um locator mock

#         async def goto(self, url, **kwargs):
#              print(f"MockPage: Navegando para {url} com kwargs: {kwargs}")
#              if "error_url" in url:
#                   raise Exception(f"Mock: Erro ao navegar para {url}")

#         async def screenshot(self, path):
#              print(f"MockPage: Salvando screenshot mock em {path}")

#         def frame_locator(self, selector):
#              print(f"MockPage: Procurando frame locator para {selector}")
#              if selector == "mock_iframe":
#                   # Um frame locator é apenas um locator que representa o iframe
#                   return self.locator(selector)
#              return None # Simula não encontrar

#         # Adicionar mock para on("console") se necessário, mas não crucial para este teste base


#     # Mock do ErrorHandler (simplificado para o teste)
#     class MockErrorHandler:
#         def __init__(self):
#             self._pause_count = 0

#         async def handle_error(self, e, step_description: str = "Passo desconhecido", data_row=None):
#             self._pause_count += 1
#             print(f"\n--- MOCK HANDLER --- (Pausa {self._pause_count})")
#             print(f"  ERRO: {e}")
#             print(f"  PASSO: {step_description}")
#             print(f"  DADOS: {data_row}")
#             print(f"  Simulando screenshot...")
#             print("---------------------\n")
#             # Simula a decisão do usuário (sem dialog real)
#             # raise SkipRecordException("Simulando Skip") # Descomente para testar o Skip
#             # raise AbortAutomationException("Simulando Abort") # Descomente para testar o Abort
#             # Por padrão, apenas "trata" o erro (printa) e permite que o erro original se propague
#             pass # Não levanta nada, o erro original vai continuar se o chamador não capturar

#     async def run_base_page_tests():
#         mock_page = MockPage()
#         mock_handler = MockErrorHandler()
#         base_page = BasePage(mock_page, mock_handler)

#         print("--- Teste de Sucesso ---")
#         try:
#              locator_success = mock_page.locator("success_locator")
#              await base_page._safe_click(locator_success, "Botão Sucesso")
#              await base_page._safe_fill(locator_success, "Teste", "Campo Sucesso")
#              await base_page._safe_select_option(locator_success, "valor", "Dropdown Sucesso")
#              await base_page._safe_press(locator_success, "Enter", "Elemento Sucesso (Enter)")
#              await base_page._safe_type_with_delay(locator_success, "Digitar", 50, "Elemento Sucesso (Digitar)")
#              await base_page._safe_wait_for_selector("success_wait_selector", step_description="Esperar Sucesso")
#              await base_page._safe_goto("https://success.com", step_description="Navegar Sucesso")
#              # Teste de iframe (frame_locator retorna locator mock)
#              await base_page._safe_switch_to_iframe("mock_iframe", "Iframe Sucesso")
#              await base_page._safe_switch_to_default_content() # Não faz nada async, só loga
#              await base_page._safe_click_by_text("Texto Botão Sucesso", "Botão Sucesso Por Texto")

#         except (AutomationError, SkipRecordException, AbortAutomationException, Exception) as e:
#              print(f"\nErro inesperado durante teste de sucesso: {e}")

#         print("\n--- Teste de Falha (Elemento Não Encontrado / Timeout) ---")
#         try:
#              locator_fail_wait = mock_page.locator("fail_selector")
#              await base_page._safe_click(locator_fail_wait, "Botão Falha (Wait Timeout)")
#         except (AutomationError, SkipRecordException, AbortAutomationException) as e:
#              print(f"Capturado exceção esperada: {e}")
#         except Exception as e:
#              print(f"Capturado EXCEÇÃO GENÉRICA inesperada: {e}")


#         print("\n--- Teste de Falha (Erro genérico no Click) ---")
#         try:
#              locator_uninteractable = mock_page.locator("uninteractable_selector")
#              await base_page._safe_click(locator_uninteractable, "Botão Falha (Uninteractable)")
#         except (AutomationError, SkipRecordException, AbortAutomationException) as e:
#              print(f"Capturado exceção esperada: {e}")
#         except Exception as e:
#              print(f"Capturado EXCEÇÃO GENÉRICA inesperada: {e}")

#         print("\n--- Teste de Falha (Wait for Selector Timeout) ---")
#         try:
#              await base_page._safe_wait_for_selector("fail_wait_selector", step_description="Esperar Falha Timeout")
#         except (AutomationError, SkipRecordException, AbortAutomationException) as e:
#              print(f"Capturado exceção esperada: {e}")
#         except Exception as e:
#              print(f"Capturado EXCEÇÃO GENÉRICA inesperada: {e}")

#         print("\n--- Teste de Falha (GoTo Error) ---")
#         try:
#             await base_page._safe_goto("error_url", step_description="Navegar Falha URL")
#         except (AutomationError, SkipRecordException, AbortAutomationException) as e:
#              print(f"Capturado exceção esperada: {e}")
#         except Exception as e:
#              print(f"Capturado EXCEÇÃO GENÉRICA inesperada: {e}")


#     asyncio.run(run_base_page_tests())