# Arquivo: app/automation/pages/procedimento_form.py (CORRIGIDO 61)
from playwright.async_api import Page, Locator
from app.automation.pages.base_page import BasePage
from app.core.logger import logger
from app.automation.error_handler import AutomationErrorHandler # Importa aqui
from app.automation.error_handler import AutomationError # Importa a exceção AutomationError
import re # Pode ser útil para procurar labels por texto parcial ou case-insensitive
# from app.automation.pages.atendimento_form import AtendimentoForm # Importa AtendimentoForm
from app.core.utils import normalize_text_for_selection
import asyncio

class ProcedimentoForm(BasePage):
    """
    Representa os campos específicos do formulário de Ficha de Procedimentos
    dentro do iframe principal.
    """
    # Seletor para o iframe principal (deve ser o mesmo usado no main_menu e common_forms)
    _ESUS_IFRAME_SELECTOR = '//iframe[@title="e-sus"]' # Exemplo

    # Seletores para campos específicos de Procedimentos dentro do iframe
    # Verifique estes seletores no seu site real
    # Código do SIGTAP (campo de texto com busca) - Usado na Aferição
    _SIGTAP_SELECTED_LIST_ITEM_SELECTOR_TEMPLATE = '.search-item.x-combo-selected:has-text("{}")'
    _SIGTAP_FIELD_XPATH = '//label[contains(text(), "Código do SIGTAP")]/following-sibling::input[contains(@class, "x-form-no-radius-right")]'
    _SIGTAP_LIST_ITEM_SELECTOR_TEMPLATE = '.search-item:has-text("{}")'
    # Seletor genérico para itens da lista de busca (aparece ao digitar SIGTAP) - Pode ser o mesmo do CIAP
    # _SEARCH_ITEM_TEXT_SELECTOR = '.search-item h3 b' # Exemplo
    # _SIGTAP_LIST_ITEM_SELECTOR = '.search-item:has-text("{}")'
    
     #-----------xxxxxxxxxxxxxxxxxxxxxxxxxx----------------#
    _SIGTAP_SUGGESTION_ITEM_XPATH_TEMPLATE = "//div[contains(@class, 'x-combo-list-inner')]//b[starts-with(normalize-space(), '{}')]"
    #Extra 01: XPath ainda mais robusto (caso o código esteja dentro de outro td)
    # _SIGTAP_SUGGESTION_ITEM_XPATH_TEMPLATE = "//div[contains(@class, 'x-combo-list-inner')]//div[contains(@class, 'search-item')]//b[starts-with(normalize-space(), '{}')]"
    #Extra 02 Ou até mais seguro ainda:
    # _SIGTAP_SUGGESTION_ITEM_XPATH_TEMPLATE = "//div[contains(@class, 'x-combo-list-inner')]//div[contains(@class, 'search-item') and contains(@class, 'x-combo-selected')]//*[self::b or self::td][starts-with(normalize-space(), '{}')]"
    #-----------xxxxxxxxxxxxxxxxxxxxxxxxxx----------------#

    # _SIGTAP_SUGGESTION_ITEM_NAME_TEMPLATE = "{} - AFERIÇÃO DE PRESSÃO ARTERIAL"
    # Seletor para o contêiner de validação do SIGTAP (se houver popup) - PEID message-box e botão OK já no common_forms ou _handle_ciap_alert?
    # Vamos reutilizar o handler de alerta do atendimento por enquanto, pois o comportamento pode ser similar

    # Exame / Procedimento (campo de texto com busca) - Usado na Saúde Sexual e Reprodutiva (Citopatológico)
    _OUTROS_SIA_EXAME_FIELD_XPATH = '//div[@peid="OutrosSiaForm.siaSelectDto"]//label[contains(text(), "Exame")]/following-sibling::input' # Exemplo baseado no seu código
    # Seletor para o contêiner de status (S/N) após selecionar Exame/Procedimento
    _OUTROS_SIA_STATUS_CONTAINER_SELECTOR = '//div[@peid="OutrosSiaForm.status"]' # Exemplo
    _STATUS_RADIO_S = './/label[text()="S"]/preceding-sibling::input[@type="radio"]' # Exemplo: radio S dentro do container
    # Seletor para o botão Confirmar após selecionar Exame/Procedimento (PEID no seu código)
    _OUTROS_SIA_CONFIRMAR_BUTTON_SELECTOR = 'div[peid="OutrosSiaAtendimentoIndividualComponentFlexList.Confirmar"] button:has-text("Confirmar")' # Exemplo


    def __init__(self, page: Page, error_handler: AutomationErrorHandler):
        super().__init__(page, error_handler)
        # Reutiliza o método de tratamento de alerta que pode ser similar

    #Versão anterior do método fill_sigtap_code, mantida para referência
    # async def fill_sigtap_code(self, iframe_frame: Locator, sigtap_code: str):
    #     """Preenche o campo Código do SIGTAP e seleciona o código (Aferição)."""
    #     logger.info(f"Preenchendo campo 'Código do SIGTAP' com: {sigtap_code}")
    #     sigtap_field_locator = iframe_frame.locator(self._SIGTAP_FIELD_XPATH)
    #     await self._safe_fill(sigtap_field_locator, sigtap_code, step_description="Campo Código do SIGTAP")
    #     await asyncio.sleep(2) # Espera para a lista de busca aparecer

    #     # Clica no item da lista de busca que corresponde ao código (texto exato)
    #     # Verifique onde a lista aparece (iframe ou documento principal)
    #     search_item_locator = self._page.locator(self._SEARCH_ITEM_TEXT_SELECTOR, has_text=sigtap_code).first
    #     # Se aparece DENTRO do iframe, use iframe_frame.locator(...)

    #     await self._safe_click(search_item_locator, step_description=f"Item '{sigtap_code}' na lista de busca do SIGTAP")
    #     await asyncio.sleep(1) # Pequena pausa após selecionar

    #     # Lida com possíveis popups de alerta após selecionar o SIGTAP (reutiliza lógica do CIAP)
    #     await self._handle_ciap_alert(self._page) # Alerta pode aparecer no contexto principal (_page)
    # async def fill_sigtap_code(self, iframe_frame: Locator, sigtap_code: str):
    #     logger.info(f"Preenchendo campo 'Código do SIGTAP' com: {sigtap_code}")
    #     sigtap_field_locator = iframe_frame.locator(self._SIGTAP_FIELD_XPATH)

    #     # XPath mais tolerante
    #     suggestion_xpath = f"//div[contains(@class, 'x-combo-list-inner')]//b[text()='{sigtap_code}']"
    #     suggestion_locator = iframe_frame.locator(suggestion_xpath)

    #     try:
    #         # Preencher o código
    #         await self._safe_fill_simule(sigtap_field_locator, sigtap_code, step_description="Campo Código do SIGTAP - Preencher")
    #         logger.debug("Aguardando a sugestão com o código aparecer na lista...")

    #         # Esperar a sugestão com o código
    #         await suggestion_locator.wait_for(state="visible", timeout=7000)

    #         # Selecionar com ↓ + Enter
    #         logger.debug("Sugestão visível. Selecionando com seta para baixo e enter...")
    #         await self._safe_press(sigtap_field_locator, 'ArrowDown', step_description="Selecionar sugestão SIGTAP - ArrowDown")
    #         await asyncio.sleep(0.2)
    #         await self._safe_press(sigtap_field_locator, 'Enter', step_description="Selecionar sugestão SIGTAP - Enter")
    #         await asyncio.sleep(1.5)

    #         # Trata alertas, se houver
    #         popup_status = await self._handle_ciap_alert(self._page)
    #         if popup_status == "handled":
    #             logger.debug("Popup tratado com sucesso.")
    #         elif popup_status == "error":
    #             logger.warning("Erro ao tratar popup de alerta SIGTAP.")

    #     except TimeoutError as e:
    #         html_dump = await iframe_frame.content()
    #         logger.error(f"Erro ao localizar sugestão para SIGTAP '{sigtap_code}'. DOM parcial:\n{html_dump[:3000]}")
    #         raise AutomationError(f"Timeout ao localizar sugestão do SIGTAP '{sigtap_code}'.") from e

    #     except Exception as e:
    #         logger.error(f"Erro ao preencher e selecionar Código do SIGTAP '{sigtap_code}': {e}", exc_info=True)
    #         raise AutomationError(f"Falha ao preencher/selecionar Código do SIGTAP '{sigtap_code}'.") from e

    async def fill_sigtap_code(self, iframe_frame: Locator, sigtap_code: str):
        logger.info(f"Preenchendo campo 'Código do SIGTAP' com: {sigtap_code}")
        sigtap_field_locator = iframe_frame.locator(self._SIGTAP_FIELD_XPATH)

        try:
            # ** 1. PREENCHER USANDO _safe_fill_simule (digitação lenta) **
            await self._safe_fill_simule(sigtap_field_locator, sigtap_code, step_description="Campo Código do SIGTAP - Preencher (Simulado)")
            logger.debug("Aguardando a sugestão com o código aparecer na lista...")

            # 2. ESPERAR A SUGESTÃO EXATA APARECER
            # O XPath que você forneceu é excelente para o item exato.
            suggestion_locator = iframe_frame.locator(self._SIGTAP_SUGGESTION_ITEM_XPATH_TEMPLATE.format(sigtap_code))
            
            await suggestion_locator.wait_for(state="visible", timeout=7000) # Timeout de 7 segundos
            logger.debug("Sugestão visível. Selecionando com seta para baixo e enter...")

            # 3. SELECIONAR COM ARROWDOWN + ENTER (no campo original, para confirmar)
            await self._safe_press(sigtap_field_locator, 'ArrowDown', step_description="Selecionar sugestão SIGTAP - ArrowDown")
            await asyncio.sleep(0.2)
            await self._safe_press(sigtap_field_locator, 'Enter', step_description="Selecionar sugestão SIGTAP - Enter")
            await asyncio.sleep(1.5) # Pausa após Enter

            # # 4. Trata alertas, se houver
            # popup_status = await self._handle_ciap_alert(self._page) # Chame do self._page para popups globais
            # if popup_status == "handled":
            #     logger.debug("Popup tratado com sucesso.")
            # elif popup_status == "error":
            #     logger.warning("Erro ao tratar popup de alerta SIGTAP.")

            logger.info(f"Código SIGTAP '{sigtap_code}' selecionado com sucesso.")

        except TimeoutError as e:
            # Captura TimeoutError se a sugestão EXATA não aparecer.
            html_dump = await iframe_frame.content()
            logger.error(f"Erro ao localizar sugestão para SIGTAP '{sigtap_code}'. Timeout de 7s excedido. DOM parcial:\n{html_dump[:3000]}")
            raise AutomationError(f"Timeout ao localizar sugestão do SIGTAP '{sigtap_code}'.") from e

        except Exception as e:
            logger.error(f"Erro ao preencher e selecionar Código do SIGTAP '{sigtap_code}': {e}", exc_info=True)
            raise AutomationError(f"Falha ao preencher/selecionar Código do SIGTAP '{sigtap_code}'.") from e


    async def fill_outros_sia_exame(self, iframe_frame: Locator, exame_code_or_text: str):
        """Preenche o campo Exame/Procedimento (Outros SIA) e seleciona na busca (Saúde Sexual)."""
        logger.info(f"Preenchendo campo 'Exame/Procedimento (Outros SIA)' com: {exame_code_or_text}")
        exame_field_locator = iframe_frame.locator(self._OUTROS_SIA_EXAME_FIELD_XPATH)
        await self._safe_fill(exame_field_locator, exame_code_or_text, step_description="Campo Exame/Procedimento (Outros SIA)")
        await asyncio.sleep(2) # Espera para a lista de busca aparecer

        # Clica no item da lista de busca
        # Verifique onde a lista aparece (iframe ou documento principal)
        search_item_locator = self._page.locator(self._SEARCH_ITEM_TEXT_SELECTOR, has_text=exame_code_or_text).first
         # Se aparece DENTRO do iframe, use iframe_frame.locator(...)
        await self._safe_click(search_item_locator, step_description=f"Item '{exame_code_or_text}' na lista de busca Outros SIA")
        await asyncio.sleep(1) # Pequena pausa após selecionar

    async def select_outros_sia_status(self, iframe_frame: Locator, status: str = "S"):
         """Seleciona o status (S/N) após escolher o Exame/Procedimento (Outros SIA)."""
         # Assume que o status desejado é "S" como no seu código original
         if status.upper() != "S":
              logger.warning(f"Status diferente de 'S' solicitado para Outros SIA ({status}). Apenas 'S' é suportado nesta função.")
              return

         logger.info(f"Selecionando Status '{status}' para Outros SIA.")
         # Encontra o container de status
         status_container_locator = iframe_frame.locator(self._OUTROS_SIA_STATUS_CONTAINER_SELECTOR)
         # Encontra o rádio 'S' dentro do container e clica no label associado
         radio_s_locator = status_container_locator.locator(self._STATUS_RADIO_S)
         label_s_locator = radio_s_locator.locator("/following-sibling::label")

         await self._safe_click(label_s_locator, step_description=f"Rádio Status '{status}' (Outros SIA)")
         # Se clicar no label não funcionar:
         # await self._safe_click(radio_s_locator, step_description=f"Rádio Status '{status}' (Outros SIA)")


    async def click_outros_sia_confirm_button(self, iframe_frame: Locator):
         """Clica no botão 'Confirmar' do bloco Outros SIA/Exame/Procedimento."""
         confirm_button_locator = iframe_frame.locator(self._OUTROS_SIA_CONFIRMAR_BUTTON_SELECTOR)
         logger.info("Clicando no botão 'Confirmar' do bloco Outros SIA.")
         await self._safe_click(confirm_button_locator, step_description="Botão 'Confirmar' Outros SIA")
         await asyncio.sleep(1) # Pequena pausa após confirmar


    async def click_confirm_button(self, iframe_frame: Locator):
        """Clica no botão 'Confirmar' da ficha de Procedimentos."""
        # Seletor para o botão Confirmar da ficha de Procedimentos (PEID no seu código)
        confirm_button_locator = iframe_frame.locator('div[peid="FichaProcedimentosDetailChildViewImpl.Confirmar"] button:has-text("Confirmar")')
        logger.info("Clicando no botão 'Confirmar' de Procedimentos.")
        await self._safe_click(confirm_button_locator, step_description="Botão 'Confirmar' Procedimentos")

        # Lida com o alerta de "Campos duplicados" (baseado no seu button_loop_confir_Proced)
        await self._handle_duplicate_fields_alert(self._page) # Alerta pode aparecer no contexto principal

    async def _handle_duplicate_fields_alert(self, page_or_frame: Page | Locator):
         """Lida com o popup de alerta 'Campos duplicados' que pode aparecer."""
         alert_container_locator = page_or_frame.locator('div[peid="message-box"]') # Reutiliza o seletor do alerta genérico
         ok_button_locator = alert_container_locator.locator('button:has-text("OK")')

         logger.debug("Verificando por popup 'Campos duplicados'...")
         try:
             # Espera um curto período pela visibilidade do contêiner do alerta E pelo texto "Campos duplicados" dentro dele
             await alert_container_locator.filter(has_text="Campos duplicados").wait_for(state="visible", timeout=3000)
             logger.info("Popup 'Campos duplicados' encontrado. Clicando em 'OK'.")
             await self._safe_click(ok_button_locator, step_description="Botão 'OK' no popup 'Campos duplicados'")
             await alert_container_locator.wait_for(state="hidden", timeout=3000) # Espera o popup desaparecer
             logger.info("Popup 'Campos duplicados' fechado.")

             # IMPORTANTE: No seu código original, se aparecia "Campos duplicados", ele tentava CLICAR NO CONFIRMAR novamente.
             # Isso é uma lógica de RETENTATIVA APÓS ERRO. Esta lógica deve estar no TaskRunner,
             # que é quem chama o click_confirm_button e captura a exceção (se _safe_click falhar)
             # ou lida com o retorno do handle_error.
             # Se _handle_duplicate_fields_alert for chamado *dentro* do _safe_click,
             # e o _safe_click falhar na primeira vez (por causa do popup bloqueando a interação,
             # mas ele não é um erro de elemento não encontrado), então o handle_error é chamado,
             # o callback é chamado. Se o usuário clica em 'Continuar', o handle_error retorna,
             # e o _safe_click original tenta novamente (o que pode ainda falhar se o popup não sumiu ou outro erro ocorreu).
             # Uma abordagem MELHOR é o TaskRunner capturar a exceção (que foi tratada pelo handler
             # e o usuário clicou 'Continuar'), e o TaskRunner decidir se tenta o passo novamente.
             # POR ORA, a lógica de retentar o Confirmar após "Campos Duplicados" NÃO está aqui,
             # ela precisará ser adicionada no TaskRunner que chama este método.

         except Exception: # Captura TimeoutError se não aparecer ou erro ao clicar/fechar
             logger.debug("Nenhum popup 'Campos duplicados' encontrado.")

    async def _select_dropdown_option(self, locator, step_description=""):
        await self._safe_press(locator, 'ArrowDown', step_description=f"{step_description} - ArrowDown")
        await asyncio.sleep(0.5)
        await self._safe_press(locator, 'Enter', step_description=f"{step_description} - Enter")
        await asyncio.sleep(2)



    # Adicione outros campos ou interações específicas dos formulários de Procedimento aqui
    # (Ex: Campos de Medidas Antropométricas se aparecerem na ficha de procedimento,
    # outros tipos de procedimentos com SIGTAP diferente, etc.)