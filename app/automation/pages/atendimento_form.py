# Arquivo: app/automation/pages/atendimento_form.py
import asyncio
from playwright.async_api import Page, Locator
from app.automation.pages.base_page import BasePage
from app.core.logger import logger
from app.automation.error_handler import AutomationErrorHandler
from app.core.errors import AutomationError
from app.core.utils import normalize_text_for_selection
import re # Pode ser útil para procurar labels por texto parcial ou case-insensitive

class AtendimentoForm(BasePage):
    """
    Representa os campos específicos dos formulários de Atendimento Individual
    dentro do iframe principal.
    """
    # Seletor para o iframe principal (deve ser o mesmo usado no main_menu e common_forms)
    _ESUS_IFRAME_SELECTOR = '//iframe[@title="e-sus"]' # Exemplo

    # Seletores para campos específicos de Atendimento Individual dentro do iframe
    # Verifique estes seletores no seu site real
    # Adiciona o seletor de label para Tipo de Atendimento
    _TIPO_ATENDIMENTO_LABEL_SELECTOR_TEMPLATE = 'label:has-text("{}")' # Usado para clicar no label do tipo de atendimento
    # Condição Avaliada (checkboxes)
    # Usaremos um template ou buscaremos por texto porque há vários checkboxes
    _CONDICAO_AVALIADA_CHECKBOX_XPATH_TEMPLATE = '//label[contains(text(), "{}")]/preceding-sibling::input[@type="checkbox"]' # Exemplo: substitui {} pelo texto parcial (e.g., "Hipertensão")
    _CONDICAO_AVALIADA_LABEL_SELECTOR_TEMPLATE = 'label:has-text("{}")'
    # CIAP2 - 01 (campo de texto com busca) - Usado no A97
    _CIAP_01_FIELD_XPATH = '//label[contains(text(), "CIAP2 - 01")]/following-sibling::input' # Exemplo
    # Seletor genérico para itens da lista de busca (aparece ao digitar CIAP)
    _SEARCH_ITEM_TEXT_SELECTOR = '.search-item h3 b' # Exemplo para buscar texto 'A97' na lista
    # Exames Solicitados/Avaliados (checkboxes) - Usado no Diabético (Ex: Hemoglobina Glicada)
    # No seu código, você clicava no 10º checkbox S-..., ou um com PEID.
    # Precisamos de um jeito mais robusto. Playwright pode encontrar elementos por texto ou contendo outros elementos.
    # Seletor para o contêiner onde ficam os checkboxes de exames (se houver um PEID ou classe)
    _EXAMES_CONTAINER_SELECTOR = '[peid="FichaAtendimentoIndividualChildForm.examesSolicitados"]' # Exemplo do seu código
    # Seletor genérico para checkboxes DENTRO do container de exames
    _EXAME_CHECKBOX_IN_CONTAINER_SELECTOR = 'input[type="checkbox"]'
    _EXAME_LABEL_IN_CONTAINER_SELECTOR = 'input[type="checkbox"] + label' # Label que segue um checkbox
    # Conduta (checkboxes)
    # Usaremos um template ou buscaremos por texto porque há vários checkboxes
    _CONDUTA_CHECKBOX_XPATH_TEMPLATE = '//label[contains(text(), "{}")]/preceding-sibling::input[@type="checkbox"]' # Exemplo: substitui {} pelo texto parcial (e.g., "Retorno agendado")
    _CONDUTA_CHECKBOX_SELECTOR_TEMPLATE = 'label:has-text("{}")'

    # Seletor para o botão Confirmar DA FICHA
    _CONFIRM_BUTTON_FICHA_SELECTOR = 'div[peid="FichaAtendimentoIndividualDetailChildViewImpl.Confirmar"] button:has-text("Confirmar")'
    # Seletor para o botão Confirmar DO BLOCO Outros SIA (usado em Saúde Repro e Diabético no seu código original)
    _CONFIRM_BUTTON_SIA_BLOCK_SELECTOR = 'div[peid="OutrosSiaAtendimentoIndividualComponentFlexList.Confirmar"] button:has-text("Confirmar")'

    # Inspecione o screenshot para encontrar um contêiner pai para "Problema / Condição avaliada".
    # Exemplo: Se houver um fieldset ou div com título "Problema / Condição avaliada"
    # _CONDICAO_AVALIADA_CONTAINER_SELECTOR = 'fieldset:has-text("Problema / Condição avaliada")' # Exemplo (VERIFIQUE!)
    _CONDICAO_AVALIADA_CONTAINER_SELECTOR = '[peid="ProblemaCondicaoAvaliadaAIForm.problemasCondicoesAvaliadas"]'
    _CONDICAO_AVALIADA_LABEL_SELECTOR_IN_CONTAINER = 'label' # XPath relativo para todos os labels dentro do contêiner
    _CONDICAO_AVALIADA_LABEL_SELECTOR_TEMPLATE = 'label:has-text("{}")' # Template para encontrar o LABEL da condição

    # ** NOVO SELETOR PARA O POPUP PADRÃO peid="message-box" **
    _MESSAGE_BOX_POPUP_SELECTOR = 'div[peid="message-box"]'
    _MESSAGE_BOX_OK_BUTTON_SELECTOR = f'{_MESSAGE_BOX_POPUP_SELECTOR} button:has-text("OK")' # Botão OK dentro deste popup


    def __init__(self, page: Page, error_handler: AutomationErrorHandler):
        super().__init__(page, error_handler)

    async def select_tipo_atendimento(self, iframe_frame: Locator, tipo_atendimento: str):
        """Seleciona o Tipo de Atendimento (Inicial, Consulta de Retorno, etc.) clicando no label associado."""
        logger.info(f"Selecionando Tipo de Atendimento: {tipo_atendimento}")

        # ** CORREÇÃO: Use a Opção 1 (label:has-text) - FINALMENTE! **
        try:
            label_selector = self._TIPO_ATENDIMENTO_LABEL_SELECTOR_TEMPLATE.format(tipo_atendimento)
            label_locator = iframe_frame.locator(label_selector)
            logger.debug(f"Tentando clicar no label para Tipo de Atendimento: {tipo_atendimento} (Selector: {label_locator.locator})")
            await self._safe_click(label_locator, step_description=f"Label Rádio Tipo Atendimento: {tipo_atendimento}")
            logger.debug(f"Label para Tipo de Atendimento '{tipo_atendimento}' clicado com sucesso.")

        except Exception as e:
            # Se chegamos aqui, significa que _safe_click falhou.
            # _safe_click já chamou o handler e re-levantou.
            # Capturamos E re-levantamos como AutomationError.
            logger.error(f"Erro ao selecionar Tipo de Atendimento '{tipo_atendimento}': {e}")
            raise AutomationError(f"Falha ao selecionar Tipo de Atendimento '{tipo_atendimento}' no iframe.") from e

    async def select_condicao_avaliada(self, iframe_frame: Locator, condicao: str):
        """
        Seleciona uma Condição Avaliada (checkbox).
        Busca por todos os labels na área relevante, normaliza o texto e compara com o valor do CSV normalizado.
        """
        logger.info(f"Selecionando Condição Avaliada: {condicao}")

        if not isinstance(condicao, str) or not condicao:
             logger.warning(f"Valor inválido ou vazio para Condição Avaliada: '{condicao}'. Pulando seleção.")
             return

        # ** NORMALIZA O TEXTO BUSCADO DO CSV PARA COMPARAÇÃO **
        condicao_normalized = normalize_text_for_selection(condicao)
        logger.debug(f"Condição Avaliada normalizada do CSV: '{condicao_normalized}'")


        try:
            # 1. Encontrar o contêiner da área de Condições Avaliadas (para limitar a busca)
            condition_container_locator = iframe_frame.locator(self._CONDICAO_AVALIADA_CONTAINER_SELECTOR)
            await condition_container_locator.wait_for(state="visible", timeout=10000) # Espera a área aparecer
            logger.debug("Contêiner de Condição Avaliada visível. Buscando labels...")

            # 2. Encontrar TODOS os labels DENTRO deste contêiner
            all_labels_locator = condition_container_locator.locator(self._CONDICAO_AVALIADA_LABEL_SELECTOR_IN_CONTAINER)
            labels_count = await all_labels_locator.count()

            found_and_clicked = False
            if labels_count > 0:
                 logger.debug(f"Encontrados {labels_count} labels na área de Condição Avaliada. Comparando textos...")
                 for i in range(labels_count):
                     label_locator = all_labels_locator.nth(i) # Pega o i-ésimo label
                     try:
                         label_text = (await label_locator.inner_text()).strip()
                         # ** NORMALIZA O TEXTO DO ITEM DA LISTA PARA COMPARAÇÃO **
                         label_text_normalized = normalize_text_for_selection(label_text)

                         logger.debug(f"  Comparando label '{label_text}' (Normalizado: '{label_text_normalized}') com '{condicao_normalized}'...")

                         if label_text_normalized == condicao_normalized:
                             logger.info(f"Label '{label_text}' encontrado para Condição Avaliada: '{condicao}'. Clicando.")
                             await self._safe_click(label_locator, step_description=f"Label Checkbox Condição Avaliada: {label_text}")
                             logger.debug(f"Label para Condição Avaliada '{label_text}' clicado com sucesso.")
                             found_and_clicked = True
                             break # Sai do loop for

                     except Exception as e:
                         logger.warning(f"Erro ao processar label {i}: {e}. Ignorando este label.")
                         # Continua para o próximo label no loop

            if not found_and_clicked:
                logger.warning(f"Não foi possível encontrar e clicar no label para Condição Avaliada: '{condicao}' (Normalizado: '{condicao_normalized}').")
                raise AutomationError(f"Condição Avaliada '{condicao}' não encontrada na lista.")


        except Exception as e:
            logger.error(f"Erro durante seleção da Condição Avaliada '{condicao}': {e}")
            raise AutomationError(f"Falha ao selecionar Condição Avaliada '{condicao}'.")  from e
        

    async def fill_ciap(self, iframe_frame: Locator, ciap_code: str):
        """Preenche o campo CIAP2 - 01 e seleciona o código."""
        logger.info(f"Preenchendo campo 'CIAP2 - 01' com: {ciap_code}")
        ciap_field_locator = iframe_frame.locator(self._CIAP_01_FIELD_XPATH)
        await self._safe_fill(ciap_field_locator, ciap_code, step_description="Campo CIAP2 - 01")
        await asyncio.sleep(2) # Espera para a lista de busca aparecer

        # Clica no item da lista de busca que corresponde ao código (texto exato)
        # Novamente, verifique se esta lista aparece no documento principal ou no iframe.
        # Assumindo que aparece no documento principal por enquanto.
        search_item_locator = self._page.locator(self._SEARCH_ITEM_TEXT_SELECTOR, has_text=ciap_code).first
        # Se aparece DENTRO do iframe, use iframe_frame.locator(...)

        await self._safe_click(search_item_locator, step_description=f"Item '{ciap_code}' na lista de busca do CIAP")
        await asyncio.sleep(1) # Pequena pausa após selecionar

        # Lida com possíveis popups de alerta após selecionar o CIAP
        await self._handle_ciap_alert(self._page) # O alerta pode aparecer no contexto principal (self._page)

    async def _handle_ciap_alert(self, page_or_frame: Page | Locator):
        """Lida com popups de alerta que podem aparecer após selecionar CIAP."""
        # Alertas em frameworks JS como ExtJS (usado no e-SUS) geralmente não são alertas nativos do navegador.
        # Eles são divs na página com botões. Procure pelo contêiner do alerta pelo PEID ou classe.
        # O PEID 'message-box' e o botão 'EsusMessages.OK'/'OK' são baseados no seu código.
        alert_container_locator = page_or_frame.locator('div[peid="message-box"]')
        ok_button_locator = alert_container_locator.locator('button:has-text("OK")') # Botão OK dentro do alerta

        logger.debug("Verificando por popup de alerta de CIAP...")
        try:
            # Espera um curto período, se o alerta aparecer, clica no OK
            await alert_container_locator.wait_for(state="visible", timeout=3000) # Espera no máximo 3 segundos
            logger.info("Popup de alerta de CIAP encontrado. Clicando em 'OK'.")
            await self._safe_click(ok_button_locator, step_description="Botão 'OK' no popup de alerta de CIAP")
            # Pode ser necessário esperar o popup desaparecer
            await alert_container_locator.wait_for(state="hidden", timeout=3000)
            logger.info("Popup de alerta de CIAP fechado.")
        except Exception: # Captura TimeoutError se não aparecer ou erro ao clicar/fechar
             logger.debug("Nenhum popup de alerta de CIAP encontrado.")


    async def select_exame(self, iframe_frame: Locator, exame_text: str = "S - Hemoglobina glicada"):
        """
        Seleciona um exame na lista (checkbox).
        Encontra pelo texto do label associado para ser mais robusto.
        """
        logger.info(f"Selecionando exame: {exame_text}")
        try:
            # Tenta encontrar o label que contém o texto do exame DENTRO do container de exames
            # ou diretamente no iframe se o container não for encontrado/usado.
            container_locator = iframe_frame.locator(self._EXAMES_CONTAINER_SELECTOR)
            if await container_locator.count() == 0:
                 logger.warning(f"Contêiner de exames ({self._EXAMES_CONTAINER_SELECTOR}) não encontrado. Buscando label diretamente no iframe.")
                 search_area_locator = iframe_frame # Busca no iframe inteiro
            else:
                 search_area_locator = container_locator.first # Busca dentro do primeiro container encontrado

            label_locator = search_area_locator.locator(self._EXAME_LABEL_IN_CONTAINER_SELECTOR, has_text=exame_text).first

            # Do label encontrado, tenta encontrar o checkbox que o precede.
            # Ou, tenta clicar diretamente no label (mais comum e eficaz).
            checkbox_locator = label_locator.locator('..').locator('input[type="checkbox"]') # Tenta encontrar o checkbox
            # Vamos tentar clicar no LABEL diretamente como a estratégia principal
            logger.debug(f"Tentando clicar no label para Exame: {exame_text} (Selector: {label_locator.locator})")
            await self._safe_click(label_locator, step_description=f"Label Checkbox Exame: {exame_text}")
            logger.debug(f"Label para Exame '{exame_text}' clicado com sucesso.")

            # Opcional: Se clicar no label não funcionar, tentar clicar no checkbox diretamente como fallback:
            # if not (await checkbox_locator.is_checked()): # Verificar se o checkbox foi marcado
            #      logger.warning(f"Label para Exame '{exame_text}' não marcou o checkbox. Tentando clicar direto no checkbox.")
            #      await self._safe_click(checkbox_locator, step_description=f"Checkbox Exame (fallback): {exame_text}")


        except Exception as e:
            logger.error(f"Erro ao selecionar exame '{exame_text}': {e}")
            raise AutomationError(f"Falha ao selecionar Exame '{exame_text}' no iframe.") from e


    async def select_conduta(self, iframe_frame: Locator, conduta: str):
        """Seleciona uma Conduta (checkbox) clicando no label associado."""
        logger.info(f"Selecionando Conduta: {conduta}")
        try:
            # Usa o seletor template label:has-text e clica no label.
            label_selector = self._CONDUTA_CHECKBOX_SELECTOR_TEMPLATE.format(conduta)
            label_locator = iframe_frame.locator(label_selector)
            logger.debug(f"Tentando clicar no label para Conduta: {conduta} (Selector: {label_locator.locator})")
            await self._safe_click(label_locator, step_description=f"Checkbox Conduta: {conduta}")
            logger.debug(f"Label para Conduta '{conduta}' clicado com sucesso.")

        except Exception as e:
            logger.error(f"Erro ao selecionar Conduta '{conduta}': {e}")
            raise AutomationError(f"Falha ao selecionar Conduta '{conduta}' no iframe.") from e

    async def click_confirm_button(self, iframe_frame: Locator):
         """Clica no botão 'Confirmar' da ficha de Atendimento Individual."""
         # Seletor para o botão Confirmar dentro do contêiner específico
         confirm_button_locator = iframe_frame.locator(self._CONFIRM_BUTTON_FICHA_SELECTOR) # Usa o novo seletor
         logger.info("Clicando no botão 'Confirmar' do Atendimento.")
         await self._safe_click(confirm_button_locator, step_description="Botão 'Confirmar' Atendimento")
         # Pode ser necessário esperar por alguma validação ou carregamento após confirmar
         await asyncio.sleep(1) # Pequena pausa


    # Adicione outros campos ou interações específicas dos formulários de Atendimento aqui
    # (Ex: Campos de Aferição de Pressão, Peso, Altura, se houverem no formulário de atendimento)