# Arquivo: app/automation/pages/common_forms.py
import asyncio
from playwright.async_api import Page, Locator
from app.automation.pages.base_page import BasePage
from app.core.logger import logger
from app.core.errors import AutomationError, ElementNotFoundError
from app.automation.error_handler import AutomationErrorHandler
import time # Ainda pode ser útil para pequenas pausas

class CommonForms(BasePage):
    """
    Representa os campos comuns a vários formulários (Atendimento/Procedimento)
    dentro do iframe principal.
    """
    # Seletor para o iframe principal (deve ser o mesmo usado no main_menu)
    _ESUS_IFRAME_SELECTOR = '//iframe[@title="e-sus"]' # Exemplo

    # Seletores para os campos comuns dentro do iframe
    # Verifique estes seletores no seu site real
    # Campo Data de Atendimento/Procedimento (rótulo "Data")
    _DATE_FIELD_XPATH = '//label[contains(text(), "Data")]/following-sibling::input' # Exemplo baseado no seu código
    # Campo Período (rótulo "Período") e seus radios
    _PERIODO_RADIO_MANHA = '//label[contains(text(), "Manhã")]/preceding-sibling::input[@type="radio"]' # Exemplo
    _PERIODO_RADIO_TARDE = '//label[contains(text(), "Tarde")]/preceding-sibling::input[@type="radio"]' # Exemplo
    _PERIODO_RADIO_NOITE = '//label[contains(text(), "Noite")]/preceding-sibling::input[@type="radio"]' # Exemplo
    # Campo CPF / CNS (rótulo "CPF / CNS do cidadão")
    _CPF_CNS_FIELD_XPATH = '//label[contains(text(), "CPF / CNS do cidadão")]/following-sibling::input' # Exemplo
    # Campo Data de Nascimento (rótulo "Data de nascimento")
    _DOB_FIELD_XPATH = '//label[contains(text(), "Data de nascimento")]/following-sibling::input' # Exemplo
    # Campo Sexo (rótulo "Sexo") - é um dropdown/combobox customizado
    # Precisa interagir com o input e selecionar da lista que aparece
    _GENDER_FIELD_XPATH = '//label[contains(text(), "Sexo")]/following-sibling::input' # Exemplo
    # Seletor genérico para itens do dropdown (lista que aparece ao digitar/clicar)
    _DROPDOWN_ITEM_SELECTOR = '.x-combo-list-item' # Exemplo de classe comum em dropdowns ExtJS
    _DROPDOWN_ITEM_SELECTED_SELECTOR = '.x-combo-list-item.x-combo-selected' # Exemplo do item selecionado
    # Campo Local de Atendimento (rótulo "Local de atendimento") - também dropdown/combobox customizado
    _LOCAL_ATENDIMENTO_FIELD_XPATH = '//label[contains(text(), "Local de atendimento")]/following-sibling::input' # Exemplo

     # ** NOVOS SELETORES PARA OS BOTÕES LIMPAR ('x') **
    # Inspecione o "x" ao lado da seta do dropdown no site real.
    # Ele provavelmente está associado ao input ou a um elemento pai próximo.
    # Exemplo: Se for um botão ou span com classe 'x-form-clear-trigger'
    _GENDER_CLEAR_BUTTON_SELECTOR = 'xpath=//label[contains(text(), "Sexo")]/following-sibling::span[@class="x-form-clear-trigger"]' # Exemplo (VERIFIQUE!)
    _LOCAL_ATENDIMENTO_CLEAR_BUTTON_SELECTOR = 'xpath=//label[contains(text(), "Local de atendimento")]/following-sibling::span[@class="x-form-clear-trigger"]' # Exemplo (VERIFIQUE!)

    def __init__(self, page: Page, error_handler: AutomationErrorHandler):
        super().__init__(page, error_handler)

    async def fill_date_field(self, iframe_frame: Locator, date_str: str):
        """Preenche o campo de data de atendimento/procedimento."""
        logger.info(f"Preenchendo campo 'Data' com: {date_str}")
        # Usa o frame_locator para interagir dentro do iframe
        date_field_locator = iframe_frame.locator(self._DATE_FIELD_XPATH)
        await self._safe_fill(date_field_locator, date_str, step_description="Campo Data")
        # Pode ser necessário enviar ENTER para confirmar a data no campo
        await self._safe_press(date_field_locator, 'Enter', step_description="Campo Data - Enter")
        await asyncio.sleep(1) # Pequena pausa após Enter pode ser útil para o campo processar

    async def select_period(self, iframe_frame: Locator, periodo: str):
        """Seleciona o período (Manhã, Tarde, Noite)."""
        logger.info(f"Selecionando período: {periodo}")
        periodo_lower = periodo.lower()
        # radio_locator = None # Não precisamos mais disso como variável temporária

        label_xpath = None # Variável para guardar o XPath do label correspondente

        # ** CORREÇÃO: Constrói o XPath do label DIRETAMENTE a partir do seletor do input **
        if periodo_lower == "manha":
            label_xpath = self._PERIODO_RADIO_MANHA + "/following-sibling::label"
        elif periodo_lower == "tarde":
            label_xpath = self._PERIODO_RADIO_TARDE + "/following-sibling::label"
        elif periodo_lower == "noite":
            label_xpath = self._PERIODO_RADIO_NOITE + "/following-sibling::label"
        else:
             logger.warning(f"Período desconhecido: '{periodo}'. Não foi possível determinar o seletor do label.")
             # ** Opcional: Se quiser usar o locator direto do rádio como fallback **
             # try:
             #      radio_locator = iframe_frame.locator(f'//label[text()="{periodo}"]/preceding-sibling::input[@type="radio"]')
             #      await self._safe_click(radio_locator, step_description=f"Rádio Período (fallback): {periodo}")
             #      return # Sai da função se o fallback funcionou
             # except Exception as e:
             #      logger.warning(f"Fallback para selecionar rádio período {periodo} falhou também: {e}")
             # Fica a critério se quer tentar o fallback ou apenas logar o aviso e continuar/falhar.
             return # Sai da função se o período é desconhecido

        # Se um label_xpath foi determinado
        if label_xpath:
             logger.debug(f"Tentando clicar no label para Período: {periodo} (XPath: {label_xpath})")
             label_locator = iframe_frame.locator(label_xpath) # Cria o locator para o label

             # Usa o _safe_click no locator do label. Se falhar, o handler será chamado.
             await self._safe_click(label_locator, step_description=f"Label Rádio Período: {periodo}")
             logger.debug(f"Label para Período '{periodo}' clicado com sucesso.")

        # Se label_xpath não foi determinado (período desconhecido), o 'return' anterior já saiu.


    async def fill_cpf_cns(self, iframe_frame: Locator, cpf_cns: str):
        """Preenche o campo CPF / CNS do cidadão."""
        logger.info(f"Preenchendo campo 'CPF / CNS' com: {cpf_cns}")
        cpf_field_locator = iframe_frame.locator(self._CPF_CNS_FIELD_XPATH)
        await self._safe_fill(cpf_field_locator, cpf_cns, step_description="Campo CPF / CNS")
        # Pode ser necessário enviar ENTER ou TAB para validar o CPF/CNS e carregar dados do cidadão
        await self._safe_press(cpf_field_locator, 'Tab', step_description="Campo CPF / CNS - Tab")
        # Pode ser necessário esperar por algum elemento aparecer ou mudar na página após validar o CPF
        # Ex: esperar o campo Nome do Cidadão ser preenchido ou visível
        # await iframe_frame.locator('seletor_campo_nome_cidadao').wait_for(state='visible', timeout=10000)
        await asyncio.sleep(2) # Pequena pausa para o sistema carregar dados (ajuste conforme necessário)


    async def fill_date_of_birth(self, iframe_frame: Locator, dob_str: str):
        """Preenche o campo Data de nascimento."""
        logger.info(f"Preenchendo campo 'Data de nascimento' com: {dob_str}")
        dob_field_locator = iframe_frame.locator(self._DOB_FIELD_XPATH)
        await self._safe_fill(dob_field_locator, dob_str, step_description="Campo Data de nascimento")
        await self._safe_press(dob_field_locator, 'Enter', step_description="Campo Data de nascimento - Enter")
        await asyncio.sleep(1) # Pequena pausa após Enter


    async def select_gender(self, iframe_frame: Locator, gender_value: int):
        """Seleciona o gênero (Sexo) a partir de um valor numérico (1:Masculino, 2:Feminino, 3:Indeterminado)."""
        gender_map = {
            1: "Masculino",
            2: "Feminino",
            3: "Indeterminado"
        }
        gender_text = gender_map.get(gender_value)

        if not gender_text:
            logger.warning(f"Valor de gênero desconhecido: {gender_value}. Não foi possível selecionar o gênero.")
            return

        logger.info(f"Selecionando gênero: {gender_text} (Valor: {gender_value})")
        gender_field_locator = iframe_frame.locator(self._GENDER_FIELD_XPATH)

        try:
            clear_button_locator = iframe_frame.locator(self._LOCAL_ATENDIMENTO_CLEAR_BUTTON_SELECTOR)
            if await clear_button_locator.count() > 0: # Verifica se o botão existe
                logger.debug("Botão Limpar (Local de atendimento) encontrado. Clicando...")
                await self._safe_click(clear_button_locator, step_description="Campo Local de atendimento - Clicar Limpar")
                await asyncio.sleep(0.5) # Pausa após limpar

            # Preenche o campo com o texto
            logger.debug(f"Preenchendo campo Sexo com '{gender_text}'...")
            await self._safe_fill(gender_field_locator, gender_text, step_description="Campo Sexo - Preencher")
            await asyncio.sleep(1)

            # Pressiona seta para baixo para abrir a lista
            logger.debug("Abrindo dropdown com ArrowDown...")
            await self._safe_press(gender_field_locator, 'ArrowDown', step_description="Campo Sexo - Abrir dropdown")
            await asyncio.sleep(1)

            # Percorre os itens do dropdown
            for _ in range(3):  # Limite máximo de tentativas
                dropdown_items = iframe_frame.locator(".x-combo-list-item")

                count = await dropdown_items.count()
                for i in range(count):
                    item = dropdown_items.nth(i)
                    item_text = (await item.inner_text()).strip()
                    item_class = await item.get_attribute("class")

                    if "x-combo-selected" in item_class and item_text == gender_text:
                        logger.debug(f"Item encontrado e selecionado: '{item_text}'. Pressionando Enter.")
                        await self._safe_press(gender_field_locator, 'Enter', step_description="Campo Sexo - Confirmar seleção")
                        await asyncio.sleep(1)
                        logger.info(f"Gênero '{gender_text}' selecionado com sucesso.")
                        return

                # Se ainda não encontrou, tenta avançar mais
                await self._safe_press(gender_field_locator, 'ArrowDown', step_description="Campo Sexo - Avançar item")
                await asyncio.sleep(1)

            logger.warning(f"Não foi possível encontrar e selecionar o gênero '{gender_text}' após várias tentativas.")

        except Exception as e:
            logger.error(f"Erro ao selecionar gênero '{gender_text}': {e}")
            raise AutomationError("Navegação Seleciona o gênero (Sexo) a partir de um valor numérico (1:Masculino, 2:Feminino, 3:Indeterminado).") from e


    async def select_local_atendimento(self, iframe_frame: Locator, local_atendimento: str):
        """
        Seleciona o Local de atendimento usando preenchimento do campo e navegação por teclas.
        Compara visualmente o item destacado com o valor esperado.
        """
        if not local_atendimento:
            logger.warning("Valor vazio para Local de atendimento. Pulando seleção.")
            return

        logger.info(f"Selecionando Local de atendimento: {local_atendimento}")
        local_field = iframe_frame.locator(self._LOCAL_ATENDIMENTO_FIELD_XPATH)

        try:
            # Preencher o campo com o texto do local
            logger.debug(f"Preenchendo campo com '{local_atendimento}'...")
            await self._safe_fill(local_field, local_atendimento, step_description="Campo Local de atendimento - Preencher")
            await asyncio.sleep(1.5)

            # Pressionar seta para baixo 2x para tentar abrir o dropdown
            logger.debug("Pressionando seta para baixo para abrir lista...")
            await self._safe_press(local_field, "ArrowDown", step_description="Campo Local - Seta para baixo 1")
            await asyncio.sleep(1)
            await self._safe_press(local_field, "ArrowDown", step_description="Campo Local - Seta para baixo 2")
            await asyncio.sleep(1)

            # Tenta localizar a opção selecionada com a classe x-combo-selected
            max_attempts = 10
            for attempt in range(max_attempts):
                logger.debug(f"Tentativa {attempt + 1} de localizar item selecionado...")
                selected_item = iframe_frame.locator('//div[contains(@class, "x-combo-list-item") and contains(@class, "x-combo-selected")]')

                if await selected_item.count() > 0:
                    selected_text = (await selected_item.first.inner_text()).strip()
                    logger.debug(f"Item selecionado visualmente: {selected_text}")

                    if selected_text.lower() == local_atendimento.lower():
                        logger.info(f"Item '{selected_text}' corresponde ao valor desejado. Clicando...")
                        await selected_item.first.click()
                        logger.info(f"Local de atendimento '{local_atendimento}' selecionado com sucesso.")
                        return
                    else:
                        # Avança na lista se não bateu
                        await self._safe_press(local_field, "ArrowDown", step_description="Campo Local - Avançar item")
                        await asyncio.sleep(1)
                else:
                    await asyncio.sleep(1)

            logger.warning(f"Não foi possível encontrar e selecionar o Local de atendimento: '{local_atendimento}'.")

        except Exception as e:
            logger.error(f"Erro ao selecionar Local de atendimento '{local_atendimento}': {e}")
            raise AutomationError("Falha na Navegação ao Selecionar Local de Atendiemnto")  from e

