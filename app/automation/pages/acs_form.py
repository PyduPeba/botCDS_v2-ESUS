# Arquivo: app/automation/pages/acs_form.py (VERSÃO v1g - Gênero por Clique)
from playwright.async_api import Page, Locator
from app.automation.pages.base_page import BasePage
from app.core.logger import logger
from app.automation.error_handler import AutomationErrorHandler, AutomationError
from playwright._impl._errors import TimeoutError
import asyncio
import re

class AcsForm(BasePage):
    """
    Representa os campos específicos do formulário de Visita Domiciliar do ACS
    dentro do iframe principal.
    """
    # --- SELETORES PARA A FICHA DE VISITA DOMICILIAR ---
    _MICRO_AREA_CONTAINER_SELECTOR = 'div[peid="FichaVisitaDomiciliarChildForm.microArea"]'
    _TIPO_IMOVEL_CONTAINER_SELECTOR = 'div[peid="FichaVisitaDomiciliarChildForm.tipoDeImovel"]'
    _SUGGESTION_ITEM_SELECTOR_TEMPLATE = "div.x-combo-list-item:has-text('{}')"

    # --- NOVOS SELETORES PARA OS CHECKBOXES ---
    _VISITA_PERIODICA_LABEL_SELECTOR = 'label:has-text("Visita periódica")'
    _PESSOA_HIPERTENSAO_LABEL_SELECTOR = 'label:has-text("Pessoa com hipertensão")'
    _DESFECHO_CONTAINER_SELECTOR = 'div[peid="FichaVisitaDomiciliarChildForm.desfechoDbEnum"]'
    _VISITA_REALIZADA_LABEL_SELECTOR = 'label:has-text("Visita realizada")'
    # --- FIM DOS NOVOS SELETORES ---

    #Botão Confirmar dentro do contêiner específico da ficha
    _CONFIRM_BUTTON_FICHA_SELECTOR = 'div[peid="FichaVisitaDomiciliarDetailChildViewImpl.Confirmar"] button:has-text("Confirmar")'

    # --- NOVO SELETOR PARA O CAMPO SEXO ---
    _GENDER_FIELD_SELECTOR = '//label[contains(text(), "Sexo")]/following-sibling::input'

    def __init__(self, page: Page, error_handler: AutomationErrorHandler):
        super().__init__(page, error_handler)
        logger.debug("Instância de AcsForm criada.")

    async def fill_micro_area(self, iframe_frame: Locator, micro_area_value: str):
        """
        Localiza o contêiner de Microárea pelo peid e preenche o campo de input interno.
        """
        logger.info(f"Preenchendo Microárea com: {micro_area_value}")
        try:
            # Localiza o contêiner e, a partir dele, o campo de input
            container_locator = iframe_frame.locator(self._MICRO_AREA_CONTAINER_SELECTOR)
            input_locator = container_locator.locator('input[type="text"]')
            
            # Usa o _safe_fill para preencher o campo
            await self._safe_fill(input_locator, micro_area_value, "Campo Microárea")

        except Exception as e:
            logger.error(f"Erro ao preencher o campo de Microárea: {e}", exc_info=True)
            # O _safe_fill já chama o handler, mas podemos adicionar um contexto extra se quisermos
            raise AutomationError(f"Falha ao preencher Microárea com valor '{micro_area_value}'.") from e

    async def select_tipo_imovel(self, iframe_frame: Locator, imovel_code: str, imovel_description: str):
        """
        Simula a digitação do código do imóvel, espera a sugestão aparecer e a seleciona
        com as teclas de seta e Enter.
        """
        full_suggestion_text = f"{imovel_code} - {imovel_description.upper()}"
        logger.info(f"Selecionando Tipo de Imóvel: {full_suggestion_text}")
        
        try:
            # 1. Localiza o contêiner e o campo de input
            container_locator = iframe_frame.locator(self._TIPO_IMOVEL_CONTAINER_SELECTOR)
            input_locator = container_locator.locator('input[type="text"]')

            # 2. Simula a digitação do código no campo
            await self._safe_fill_simule(input_locator, imovel_code, f"Campo Tipo de Imóvel - Digitar código '{imovel_code}'")

            # 3. Aguarda a sugestão correta aparecer na tela
            # A lista de sugestões geralmente aparece no contexto da página principal, não do iframe
            suggestion_locator = iframe_frame.locator(self._SUGGESTION_ITEM_SELECTOR_TEMPLATE.format(full_suggestion_text)).last
            await suggestion_locator.wait_for(state="visible", timeout=7000)
            logger.debug(f"Sugestão '{full_suggestion_text}' visível. Selecionando...")

            await self._safe_click(suggestion_locator, f"Sugestão Tipo de Imóvel: {full_suggestion_text}")

            # # 4. Pressiona a seta para baixo e Enter no campo de input para confirmar a seleção
            # await self._safe_press(input_locator, 'ArrowDown', "Selecionar sugestão Tipo de Imóvel - Seta para Baixo")
            # await asyncio.sleep(0.2)
            # await self._safe_press(input_locator, 'Enter', "Confirmar sugestão Tipo de Imóvel - Enter")
            # await asyncio.sleep(1) # Pausa para garantir que o valor foi processado

        except TimeoutError:
            logger.error(f"Timeout: A sugestão '{full_suggestion_text}' não apareceu após digitar '{imovel_code}'.")
            raise AutomationError(f"Timeout ao buscar a sugestão para o tipo de imóvel '{full_suggestion_text}'.")
        except Exception as e:
            logger.error(f"Erro ao selecionar o Tipo de Imóvel: {e}", exc_info=True)
            raise AutomationError(f"Falha ao selecionar o tipo de imóvel '{full_suggestion_text}'.") from e
        
    async def select_motivo_visita_periodica(self, iframe_frame: Locator):
        """Marca o checkbox 'Visita periódica' buscando o label diretamente no iframe."""
        logger.info("Selecionando motivo da visita: 'Visita periódica'")
        try:
            label_locator = iframe_frame.locator(self._VISITA_PERIODICA_LABEL_SELECTOR)
            await self._safe_click(label_locator, "Checkbox Motivo da Visita: Visita periódica")
        except Exception as e:
            logger.error(f"Erro ao selecionar 'Visita periódica': {e}", exc_info=True)
            raise AutomationError("Falha ao selecionar o motivo da visita 'Visita periódica'.") from e

    async def select_acompanhamento_hipertensao(self, iframe_frame: Locator):
        """Marca o checkbox 'Pessoa com hipertensão' buscando o label diretamente no iframe."""
        logger.info("Selecionando acompanhamento: 'Pessoa com hipertensão'")
        try:
            label_locator = iframe_frame.locator(self._PESSOA_HIPERTENSAO_LABEL_SELECTOR)
            await self._safe_click(label_locator, "Checkbox Acompanhamento: Pessoa com hipertensão")
        except Exception as e:
            logger.error(f"Erro ao selecionar 'Pessoa com hipertensão': {e}", exc_info=True)
            raise AutomationError("Falha ao selecionar o acompanhamento 'Pessoa com hipertensão'.") from e
        
    async def select_desfecho_visita_realizada(self, iframe_frame: Locator):
        """Localiza o contêiner de Desfecho e marca 'Visita realizada'."""
        logger.info("Selecionando desfecho: 'Visita realizada'")
        try:
            container_locator = iframe_frame.locator(self._DESFECHO_CONTAINER_SELECTOR)
            label_locator = container_locator.locator(self._VISITA_REALIZADA_LABEL_SELECTOR)
            await self._safe_click(label_locator, "Checkbox Desfecho: Visita realizada")
        except Exception as e:
            logger.error(f"Erro ao selecionar 'Visita realizada': {e}", exc_info=True)
            raise AutomationError("Falha ao selecionar o desfecho 'Visita realizada'.") from e
        
    async def click_confirm_button_acs(self, iframe_frame: Locator):
         """Clica no botão 'Confirmar' da ficha de Atendimento Individual."""
         # Seletor para o botão Confirmar dentro do contêiner específico
         confirm_button_locator = iframe_frame.locator(self._CONFIRM_BUTTON_FICHA_SELECTOR) # Usa o novo seletor
         logger.info("Clicando no botão 'Confirmar' do Atendimento.")
         await self._safe_click(confirm_button_locator, step_description="Botão 'Confirmar' Atendimento")
         # Pode ser necessário esperar por alguma validação ou carregamento após confirmar
         await asyncio.sleep(1) # Pequena pausa

    async def select_gender_acs(self, iframe_frame: Locator, gender_value: int):
        """
        Seleciona o gênero (Sexo) simulando a digitação e clicando na sugestão.
        """
        gender_map = {1: "Masculino", 2: "Feminino", 3: "Indeterminado"}
        gender_text = gender_map.get(gender_value)

        if not gender_text:
            logger.warning(f"Valor de gênero desconhecido: {gender_value}. Pulando seleção.")
            return

        logger.info(f"Selecionando gênero (ACS): {gender_text}")
        
        try:
            # 1. Localiza o campo de input para "Sexo"
            gender_field_locator = iframe_frame.locator(self._GENDER_FIELD_SELECTOR)

            # 2. Simula a digitação do texto (ex: "Feminino")
            await self._safe_fill_simule(gender_field_locator, gender_text, f"Campo Sexo - Digitar '{gender_text}'")

            # 3. Localiza a sugestão correspondente na lista
            suggestion_locator = iframe_frame.locator(
                self._SUGGESTION_ITEM_SELECTOR_TEMPLATE.format(gender_text)
            ).last

            # 4. Clica diretamente na sugestão
            await self._safe_click(suggestion_locator, f"Item da lista de sugestão: {gender_text}")
            
            await asyncio.sleep(1) # Pausa para garantir que o valor foi processado

        except TimeoutError:
            logger.error(f"Timeout: A sugestão '{gender_text}' não apareceu após a digitação.")
            raise AutomationError(f"Timeout ao buscar a sugestão para o gênero '{gender_text}'.")
        except Exception as e:
            logger.error(f"Erro ao selecionar o gênero '{gender_text}': {e}", exc_info=True)
            raise AutomationError(f"Falha ao selecionar o gênero '{gender_text}'.") from e