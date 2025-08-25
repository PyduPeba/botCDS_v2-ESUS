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
    _ALL_S_CHECKBOXES_IN_EXAMES_SELECTOR = 'div.x-form-check-wrap:has(label:has-text("S")) input[type="checkbox"]' # Seleciona o input
    _ALL_S_LABELS_IN_EXAMES_SELECTOR = 'div.x-form-check-wrap:has(label:has-text("S")) label' # Seleciona o label (para clicar)
    # Seletor genérico para checkboxes DENTRO do container de exames
    _EXAME_CHECKBOX_IN_CONTAINER_SELECTOR = 'input[type="checkbox"]'
    _EXAME_LABEL_IN_CONTAINER_SELECTOR = 'input[type="checkbox"] + label' # Label que segue um checkbox
    _EXAME_LABEL_SELECTOR_IN_CONTAINER = 'label'
    _HEMOGLOBINA_GLICADA_LABEL_SELECTOR = 'label:has-text("A - Hemoglobina glicada")'
    _GENERIC_S_CHECKBOX_LABEL_SELECTOR_IN_EXAMES = 'label:has-text("S")'
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

    _CONDUTA_FIXA_LABEL_SELECTOR = 'label:has-text("Retorno para consulta agendada")'


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


    async def select_exame(self, iframe_frame: Locator, exame_text: str = "A - Hemoglobina glicada", s_checkbox_position: int = 10):
        """
        Seleciona um checkbox "S" específico (pela posição) dentro da seção de exames.
        O 'exame_text' é usado para logar qual exame estamos marcando o "S" para.
        """
        logger.info(f"Selecionando o {s_checkbox_position}º checkbox 'S' para o exame: {exame_text}.")

        if not isinstance(exame_text, str) or not exame_text:
             logger.warning(f"Valor inválido ou vazio para Exame: '{exame_text}'. Pulando seleção.")
             # Não levanta erro fatal aqui, apenas warning. A tarefa Diabético continua.
             return


        try:
            # 1. Encontrar o contêiner da área de Exames (já corrigido)
            container_locator = iframe_frame.locator(self._EXAMES_CONTAINER_SELECTOR)
            await container_locator.wait_for(state="visible", timeout=10000) # Espera a área aparecer
            logger.debug("Contêiner de Exames visível. Buscando checkboxes 'S'...")

            # 2. Encontrar TODOS os labels "S" dentro deste contêiner
            all_s_labels_locator = container_locator.locator(self._ALL_S_LABELS_IN_EXAMES_SELECTOR)
            s_labels_count = await all_s_labels_locator.count()

            if s_labels_count == 0:
                 logger.warning(f"Nenhum label 'S' encontrado na seção de Exames. Não é possível selecionar o {s_checkbox_position}º 'S'.")
                 raise AutomationError(f"Nenhum checkbox 'S' encontrado na seção de Exames.")

            if s_checkbox_position <= 0 or s_checkbox_position > s_labels_count:
                 logger.warning(f"Posição {s_checkbox_position} para checkbox 'S' está fora do range (1 a {s_labels_count}). Não é possível selecionar.")
                 raise AutomationError(f"Posição {s_checkbox_position} para checkbox 'S' é inválida.")

            # 3. Clicar no N-ésimo label "S"
            target_s_label_locator = all_s_labels_locator.nth(s_checkbox_position - 1) # nth é 0-indexed
            
            await self._safe_click(target_s_label_locator, step_description=f"Checkbox 'S' na posição {s_checkbox_position} para Exame: {exame_text}")
            logger.debug(f"Checkbox 'S' na posição {s_checkbox_position} clicado com sucesso para Exame '{exame_text}'.")
            await asyncio.sleep(1) # Pausa após clicar no S


        except Exception as e:
            logger.error(f"Erro durante seleção do {s_checkbox_position}º checkbox 'S' para o exame '{exame_text}': {e}", exc_info=True)
            raise AutomationError(f"Falha ao selecionar {s_checkbox_position}º checkbox 'S' para Exame '{exame_text}' no iframe.") from e



    #Versão anterior que usava ARQUIVO CSV com nomes de condutas
    # async def select_conduta(self, iframe_frame: Locator, conduta: str):
    #     """Seleciona uma Conduta (checkbox) clicando no label associado."""
    #     logger.info(f"Selecionando Conduta: {conduta}")
    #     try:
    #         # Usa o seletor template label:has-text e clica no label.
    #         label_selector = self._CONDUTA_CHECKBOX_SELECTOR_TEMPLATE.format(conduta)
    #         label_locator = iframe_frame.locator(label_selector)
    #         logger.debug(f"Tentando clicar no label para Conduta: {conduta} (Selector: {label_locator.locator})")
    #         await self._safe_click(label_locator, step_description=f"Checkbox Conduta: {conduta}")
    #         logger.debug(f"Label para Conduta '{conduta}' clicado com sucesso.")

    #     except Exception as e:
    #         logger.error(f"Erro ao selecionar Conduta '{conduta}': {e}")
    #         raise AutomationError(f"Falha ao selecionar Conduta '{conduta}' no iframe.") from e
    async def select_conduta(self, iframe_frame: Locator, conduta: str): # conduta: str ainda existe como parâmetro, mas será ignorado
        """
        Seleciona a Conduta fixa "Retorno para consulta agendada".
        """
        fixed_conduta_text = "Retorno para consulta agendada"
        logger.info(f"Selecionando Conduta FIXA: {fixed_conduta_text}")

        # ** OPCIONAL: Se quiser que o parâmetro 'conduta' ainda seja verificado ou logado **
        # logger.debug(f"Conduta recebida do CSV (ignorada): '{conduta}'")
        # if conduta != fixed_conduta_text:
        #     logger.warning(f"Conduta do CSV '{conduta}' difere da conduta fixa '{fixed_conduta_text}'. Usando fixa.")

        try:
            # ** 1. BUSCAR E CLICAR NO LABEL DA CONDUTA FIXA **
            label_locator = iframe_frame.locator(self._CONDUTA_FIXA_LABEL_SELECTOR)
            logger.debug(f"Tentando clicar no label para Conduta FIXA: {fixed_conduta_text} (Selector: {label_locator.locator})")
            await self._safe_click(label_locator, step_description=f"Checkbox Conduta: {fixed_conduta_text}")
            logger.debug(f"Label para Conduta FIXA '{fixed_conduta_text}' clicado com sucesso.")

        except Exception as e:
            logger.error(f"Erro ao selecionar Conduta FIXA '{fixed_conduta_text}': {e}", exc_info=True)
            raise AutomationError(f"Falha ao selecionar Conduta FIXA '{fixed_conduta_text}' no iframe.") from e

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