# Arquivo: app/automation/pages/main_menu.py (CORRIGIDO 54)
import asyncio
from playwright.async_api import Page, Locator
from app.automation.pages.base_page import BasePage
from app.core.logger import logger
from app.automation.error_handler import AutomationErrorHandler, AutomationError # Importa aqui
import time # Ainda usaremos time.sleep para pausas longas onde não há um elemento específico para esperar
from playwright._impl._errors import TimeoutError # Importa TimeoutError para capturar específico

class MainMenu(BasePage):
    """
    Representa a navegação nos menus principais do sistema e-SUS.
    """
    # Seletores para os elementos do menu
    # Verifique estes seletores no seu site real
    # _MENU_MODULO_SELECTOR = 'div:has-text("Módulos")' # Exemplo baseado no seu CSS selector original
    # Baseado no screenshot, é o botão que tem o texto "Adicionar cidadão"
    _ADD_BUTTON_IN_FICHA_SELECTOR = 'button:has-text("Adicionar")'
    # _HOVER_ELEMENT_SELECTOR = '[data-cy="SideMenu.toggle"]'# Exemplo: Assume que o mesmo elemento de clique antigo agora usa hover
    _EXPAND_MENU_BUTTON_XPATH = '/html/body/div[1]/div/div[3]/div[1]/div/div/div/span/button/span' # Exemplo do seu código
    _CDS_MENU_ITEM_SELECTOR = '[data-cy="SideMenu.CDS"]'
    _ATENDIMENTO_INDIVIDUAL_MENU_ITEM_SELECTOR = '[data-cy="SideMenu.Atendimento individual"]'
    _PROCEDIMENTOS_MENU_ITEM_SELECTOR = '[data-cy="SideMenu.Procedimentos"]' # Exemplo

    _MENU_LATERAL_CONTAINER_SELECTOR = 'nav.css-1csmvn1'
    # Seletor genérico para o iframe principal que contém os formulários
    _ESUS_IFRAME_SELECTOR = '//iframe[@title="e-sus"]' # Exemplo do seu código

    _OPTION_ATENDIMENTO_INDIVIDUAL_SELECTOR = 'text="Atendimento individual"' # Exemplo
    _OPTION_FICHA_PROCEDIMENTOS_SELECTOR = 'text="Ficha de Procedimentos"' # Exemplo
    # Seletor genérico para itens desta lista (pode ser '.x-menu-item', '.dropdown-item', etc.)
    _TYPE_FICHA_OPTIONS_SELECTOR = '.alguma-classe-do-item-de-menu' # Placeholder
    _FINALIZE_RECORDS_BUTTON_SELECTOR = 'button:has-text("Finalizar registros")'

    def __init__(self, page: Page, error_handler: AutomationErrorHandler):
        super().__init__(page, error_handler)

    async def _click_center_of_page(self, step_description: str = "Clicar no centro da tela"):
        """Mover mouse e clicar no centro da página para tentar fechar popups/menus."""
        page_width = self._page.viewport_size['width'] if self._page.viewport_size else 1280
        page_height = self._page.viewport_size['height'] if self._page.viewport_size else 720
        center_x = page_width // 2
        center_y = page_height // 2

        logger.debug(f"Clicando no centro da tela ({center_x}, {center_y}) para {step_description}...")
        try:
             await self._page.mouse.move(center_x, center_y)
             await self._page.mouse.click(center_x, center_y)
             logger.debug(f"Clique no centro da tela realizado para {step_description}.")
             await asyncio.sleep(0.5) # Pequena pausa após o clique
        except Exception as e:
             logger.warning(f"Falha ao clicar no centro da tela para {step_description}: {e}")
             # Esta falha não é crítica, apenas loga e continua.

    async def _perform_menu_navigation_steps(self, target_item_selector: str, target_item_desc: str) -> bool:
         """
         Executa os passos de navegação no menu lateral (CDS -> Item alvo).
         Assume que o menu lateral JÁ ESTÁ VISÍVEL.
         Retorna True se bem-sucedido, False caso contrário. Não chama o handler em caso de falha.
         """
         try:
             logger.debug(f"Executando passos internos de navegação do menu lateral para {target_item_desc}...")
             cds_item_locator = self._page.locator(self._CDS_MENU_ITEM_SELECTOR)
             await cds_item_locator.wait_for(state="visible", timeout=5000)
             await self._safe_click(cds_item_locator, f"Item Menu Lateral CDS (antes de {target_item_desc})")
             await asyncio.sleep(1) # Pausa para sub-menu aparecer

             target_item_locator = self._page.locator(target_item_selector)
             await target_item_locator.wait_for(state="visible", timeout=5000)
             await self._safe_click(target_item_locator, target_item_desc)

             logger.debug(f"Passos internos de navegação do menu lateral para {target_item_desc} bem-sucedidos.")
             return True # Sucesso

         except Exception as e:
              logger.warning(f"Falha nos passos internos de navegação do menu lateral para {target_item_desc}: {e}")
              return False


    async def _select_ficha_type_steps(self, option_selector: str, option_desc: str):
         """
         Clica no botão 'Adicionar' (na Lista de atendimentos) e seleciona o tipo de ficha.
         Assume que o robô ESTÁ NA TELA "Lista de atendimentos" e o menu lateral está fechado.
         Chama o handler se falhar.
         """
         logger.info(f"Clicando no botão 'Adicionar' e selecionando '{option_desc}'.")
         try:
             # Clicar no botão "Adicionar" na Lista de Atendimentos
             add_button_locator = self._page.locator(self._ADD_BUTTON_IN_FICHA_SELECTOR) # Usamos o seletor genérico para "Adicionar"
             await add_button_locator.wait_for(state="visible", timeout=10000)
             await self._safe_click(add_button_locator, "Botão 'Adicionar' (para abrir tipo de ficha)")
             await asyncio.sleep(1) # Espera o menu/lista de opções de tipo de ficha aparecer

             # Selecionar a opção de tipo de ficha desejada
             option_locator = self._page.locator(option_selector)
             await option_locator.wait_for(state="visible", timeout=5000)
             await self._safe_click(option_locator, f"Opção '{option_desc}' na lista de tipos de ficha")
             await asyncio.sleep(2) # Espera o formulário carregar dentro do iframe

             logger.debug(f"Seleção do tipo de ficha '{option_desc}' bem-sucedida.")

         except Exception as e:
             await self._handler.handle_error(e, step_description=f"Falha ao clicar 'Adicionar' ou selecionar '{option_desc}'.")
             raise e # Re-levanta para a Task


    async def navigate_to_atendimento_individual(self) -> Locator:
        """
        Navega para a seção de Atendimento Individual (formulário).
        Inclui navegação no menu lateral, FECHA O MENU LATERAL,
        clica em "Adicionar" e seleciona o tipo de ficha.
        Retorna o FrameLocator do iframe.
        """
        logger.info("Iniciando navegação completa para formulário de Atendimento Individual.")

        menu_navigation_successful = False

        # --- Estratégia Única: Acessar o menu lateral que deve estar sempre visível ---
        logger.debug("Tentando estratégia de hover para abrir menu lateral...")
        try:
            menu_container_locator = self._page.locator(self._MENU_LATERAL_CONTAINER_SELECTOR)
            await menu_container_locator.wait_for(state="visible", timeout=5000) # Espera o menu lateral estar escondido
            logger.debug("Contêiner do menu lateral visível. Clicando nos itens...")

            # Executa os passos internos de navegação do menu lateral (CDS -> Atendimento Individual)
            # _perform_menu_navigation_steps já cuida do clique em CDS e no item alvo.
            menu_navigation_successful = await self._perform_menu_navigation_steps(
                self._ATENDIMENTO_INDIVIDUAL_MENU_ITEM_SELECTOR,
                "Item Menu Lateral Atendimento Individual (após CDS)"
            )
            if menu_navigation_successful:
                 logger.debug("Navegação do menu lateral bem-sucedida.")

        except Exception as e:
            # Se a navegação no menu lateral falhar, loga e levanta erro.
            logger.error(f"Falha na navegação do menu lateral para Atendimento Individual: {e}.")
            await self._handler.handle_error(e, step_description="Navegação para formulário de Atendimento Individual (Menu Lateral).")
            raise AutomationError(f"Navegação inicial para a tela da ficha falhou (menu lateral inacessível): {e}") from e

        
        # --- FLUXO PÓS-NAVEGAÇÃO DE MENU LATERAL BEM-SUCEDIDA ---
        if menu_navigation_successful:
             # 1. Tentar fechar o menu lateral (clicando no centro da tela)
             logger.debug("Navegação do menu lateral concluída. Tentando fechar menu lateral clicando no centro.")
             await self._click_center_of_page(step_description="Fechar menu lateral")
             await asyncio.sleep(0.5) # Pequena pausa após o clique no centro

             # 2. Clicar em "Adicionar" e selecionar o tipo de ficha
             # (Este método _select_ficha_type_steps já contém tratamento de erro com o handler)
            #  await self._select_ficha_type_steps(self._OPTION_ATENDIMENTO_INDIVIDUAL_SELECTOR, "Atendimento individual")

             # 3. Após selecionar o tipo de ficha com sucesso, espera pelo iframe e retorna seu FrameLocator.
             iframe_frame = await self._safe_switch_to_iframe(self._ESUS_IFRAME_SELECTOR, "Iframe Atendimento Individual (após selecionar tipo)")
             logger.info("Navegação para Atendimento Individual (formulário) concluída.")
             return iframe_frame

        else:
            # Se a navegação no menu lateral falhou (ambas as estratégias), levanta erro.
            raise AutomationError("Navegação inicial para a tela da ficha falhou (menu lateral inacessível).")


    async def navigate_to_procedimentos(self) -> Locator:
        """
        Navega para a seção de Ficha de Procedimentos (formulário).
        Assume que o menu lateral já está visível ou se torna visível por navegação anterior.
        Clica em "Adicionar" e seleciona o tipo de ficha. Retorna o FrameLocator do iframe.
        """
        logger.info("Iniciando navegação completa para formulário de Procedimentos.")

        menu_navigation_successful = False

        # --- Estratégia Única: Acessar o menu lateral que deve estar sempre visível ---
        logger.debug("Tentando acessar o menu lateral que deve estar sempre visível (Procedimentos).")
        try:
            menu_container_locator = self._page.locator(self._MENU_LATERAL_CONTAINER_SELECTOR)
            await menu_container_locator.wait_for(state="visible", timeout=10000)
            logger.debug("Contêiner do menu lateral visível (Procedimentos). Prosseguindo...")

            menu_navigation_successful = await self._perform_menu_navigation_steps(
                self._PROCEDIMENTOS_MENU_ITEM_SELECTOR,
                "Item Menu Lateral Procedimentos (após CDS)"
            )
            if menu_navigation_successful:
                 logger.debug("Navegação do menu lateral bem-sucedida (Procedimentos).")

        except Exception as e:
            logger.error(f"Falha na navegação do menu lateral para Procedimentos: {e}.")
            await self._handler.handle_error(e, step_description="Navegação para formulário de Procedimentos (Menu Lateral).")
            raise AutomationError(f"Navegação inicial para a tela da ficha (Procedimentos) falhou (menu lateral inacessível): {e}") from e


        # # --- Estratégia Alternativa: Clique direto no elemento que abre o menu ---
        # if not menu_navigation_successful:
        #     logger.debug("Tentando estratégia alternativa (clique direto no elemento que abre o menu - Procedimentos)...")
        #     try:
        #         click_alternative_locator = self._page.locator(self._HOVER_ELEMENT_SELECTOR)
        #         await click_alternative_locator.wait_for(state="visible", timeout=10000)
        #         await self._safe_click(click_alternative_locator, "Elemento que abre menu (alternativa clique Procedimentos)")
        #         menu_container_locator = self._page.locator(self._MENU_LATERAL_CONTAINER_SELECTOR)
        #         await menu_container_locator.wait_for(state="visible", timeout=5000)
        #         await asyncio.sleep(0.5)
        #         logger.debug("Menu lateral container visível (alternativa Procedimentos).")

        #         menu_navigation_successful = await self._perform_menu_navigation_steps(
        #             self._PROCEDIMENTOS_MENU_ITEM_SELECTOR,
        #             "Item Menu Lateral Procedimentos (após CDS alternativa)"
        #         )
        #         if menu_navigation_successful:
        #              logger.debug("Navegação do menu lateral (estratégia alternativa) bem-sucedida (Procedimentos).")

        #     except Exception as e:
        #          logger.error(f"Estratégia alternativa para abrir menu também falhou (Procedimentos): {e}.")


        # --- FLUXO PÓS-NAVEGAÇÃO DE MENU LATERAL BEM-SUCEDIDA ---
        if menu_navigation_successful:
             # 1. Tentar fechar o menu lateral (clicando no centro da tela)
             logger.debug("Navegação do menu lateral concluída (Procedimentos). Tentando fechar menu lateral clicando no centro.")
             await self._click_center_of_page(step_description="Fechar menu lateral (Procedimentos)")
             await asyncio.sleep(0.5)

            #  # 2. Clicar em "Adicionar" e selecionar o tipo de ficha
            #  await self._select_ficha_type_steps(self._OPTION_FICHA_PROCEDIMENTOS_SELECTOR, "Ficha de Procedimentos")

             # 3. Após selecionar o tipo de ficha com sucesso, espera pelo iframe e retorna seu FrameLocator.
             iframe_frame = await self._safe_switch_to_iframe(self._ESUS_IFRAME_SELECTOR, "Iframe Procedimentos (após selecionar tipo)")
             logger.info("Navegação para Procedimentos (formulário) concluída.")
             return iframe_frame

        else:
            raise AutomationError("Navegação inicial para a tela da ficha (Procedimentos) falhou (menu lateral inacessível).")

    
         
    # Adicionar um método auxiliar para clicar no centro da tela
    # async def _click_center_of_page(self, step_description: str = "Clicar no centro da tela"):
    #     """Mover mouse e clicar no centro da página para tentar fechar popups/menus."""
    #     page_width = self._page.viewport_size['width'] if self._page.viewport_size else 1280
    #     page_height = self._page.viewport_size['height'] if self._page.viewport_size else 720
    #     center_x = page_width // 2
    #     center_y = page_height // 2

    #     logger.debug(f"Clicando no centro da tela ({center_x}, {center_y}) para {step_description}...")
    #     try:
    #          # Usa force=True para tentar clicar mesmo se outro elemento estiver no caminho (cuidado!)
    #          # Ou move o mouse primeiro, depois clica.
    #          await self._page.mouse.move(center_x, center_y)
    #          await self._page.mouse.click(center_x, center_y)
    #          logger.debug(f"Clique no centro da tela realizado para {step_description}.")
    #          await asyncio.sleep(0.5) # Pequena pausa após o clique

    #     except Exception as e:
    #          logger.warning(f"Falha ao clicar no centro da tela para {step_description}: {e}")
    #          # Esta falha não é crítica, então apenas loga e continua.

    


    #     # --- Estratégia Alternativa: Clique direto no elemento que abre o menu ---
    #     # Este bloco AGORA está no mesmo nível do try/except da estratégia principal.
    #     if not menu_navigation_successful:
    #         logger.debug("Tentando estratégia alternativa (clique direto no elemento que abre o menu)...")
    #         try:
    #             click_alternative_locator = self._page.locator(self._HOVER_ELEMENT_SELECTOR) # Assumindo que é o mesmo elemento
    #             await click_alternative_locator.wait_for(state="visible", timeout=10000)
    #             await self._safe_click(click_alternative_locator, "Elemento que abre menu (alternativa clique)")
    #             menu_container_locator = self._page.locator(self._MENU_LATERAL_CONTAINER_SELECTOR)
    #             await menu_container_locator.wait_for(state="visible", timeout=5000)
    #             await asyncio.sleep(0.5)
    #             logger.debug("Menu lateral container visível (alternativa).")

    #             # Tenta executar os passos internos de navegação do menu lateral (CDS -> Atendimento Individual)
    #             menu_navigation_successful = await self._perform_menu_navigation_steps(
    #                 self._ATENDIMENTO_INDIVIDUAL_MENU_ITEM_SELECTOR,
    #                 "Item Menu Lateral Atendimento Individual (após CDS alternativa)"
    #             )
    #             if menu_navigation_successful:
    #                  logger.debug("Navegação do menu lateral (estratégia alternativa) bem-sucedida.")

    #         except Exception as e:
    #              # Se a alternativa também falhar, loga ERRO.
    #              logger.error(f"Estratégia alternativa para abrir menu também falhou: {e}.")
    #              # menu_navigation_successful já é False.
    #              # Nenhuma estratégia funcionou, não chamamos handler AQUI. A exceção
    #              # final será levantada após o if menu_navigation_successful abaixo.


    #     # --- CLICAR NO CENTRO PARA FECHAR MENU (SE NECESSÁRIO) ---
    #     # Este passo SÓ DEVE ACONTECER SE A NAVEGAÇÃO DO MENU LATERAL FOI BEM-SUCEDIDA
    #     # Este bloco AGORA está no mesmo nível dos try/except das estratégias.
    #     if menu_navigation_successful:
    #          logger.debug("Navegação do menu lateral concluída. Tentando fechar menu lateral clicando no centro.")
    #          await self._click_center_of_page(step_description="Fechar menu lateral")
    #          await asyncio.sleep(0.5)

    #          # --- CLICAR "Adicionar" e SELECIONAR TIPO DE FICHA ---
    #          # Este passo SÓ DEVE ACONTECER SE CLICAR NO CENTRO FOI BEM-SUCEDIDO (implicito no if)
    #          # E a navegação do menu lateral foi bem-sucedida.
    #          # Chama o método que clica "Adicionar" e seleciona o tipo de ficha.
    #          # Este método _select_ficha_type_steps tem tratamento de erro interno com o handler.
    #          # Se ele falhar, levantará uma exceção que a BaseTask capturará.
            

    #          # Após selecionar o tipo de ficha com sucesso, espera pelo iframe e retorna seu FrameLocator.
    #          iframe_frame = await self._safe_switch_to_iframe(self._ESUS_IFRAME_SELECTOR, "Iframe Atendimento Individual (após selecionar tipo)")
    #          logger.info("Navegação para Atendimento Individual (formulário) concluída.")
    #          return iframe_frame # Retorna o FrameLocator

    #     else:
    #         # Se a navegação no menu lateral falhou (ambas as estratégias),
    #         # levantamos um erro final AQUI para que a BaseTask saiba que a navegação inicial falhou.
    #         # Os erros específicos já foram logados nos excepts das estratégias.
    #         raise AutomationError("Navegação inicial para a tela da ficha falhou (menu lateral inacessível).")


    
    async def click_add_button_in_iframe(self, iframe_frame: Locator):
        """Clica no botão 'Adicionar' dentro do iframe (comum a atendimentos e procedimentos)."""
        # Usa o frame_locator recebido para interagir DENTRO do iframe
        add_button_locator = iframe_frame.locator(self._ADD_BUTTON_IN_FICHA_SELECTOR) # Exemplo de seletor para o botão
        logger.info("Clicando no botão 'Adicionar' dentro do iframe.")
        await self._safe_click(add_button_locator, "Botão 'Adicionar' no Iframe")

    async def click_save_button_in_iframe(self, iframe_frame: Locator):
         """Clica no botão 'Salvar' dentro do iframe."""
         save_button_locator = iframe_frame.locator('button:has-text("Salvar")')
         logger.info("Clicando no botão 'Salvar' dentro do iframe.")
         # O botão salvar pode levar tempo, ajuste o timeout no safe_click se necessário
         await self._safe_click(save_button_locator, "Botão 'Salvar' no Iframe")

    async def click_finalize_records_button_in_iframe(self, iframe_frame: Locator):
         """Clica no botão 'Finalizar registros' dentro do iframe."""
         finalize_button_locator = iframe_frame.locator(self._FINALIZE_RECORDS_BUTTON_SELECTOR)
         logger.info("Clicando no botão 'Finalizar registros' dentro do iframe.")
         await self._safe_click(finalize_button_locator, "Botão 'Finalizar registros' no Iframe")


    # Note: Mudar de volta para o conteúdo principal é feito implicitamente
    # ao usar métodos em `self._page` novamente após trabalhar no frame.
    # Podemos ter um método _safe_switch_to_default_content() na BasePage apenas para logging/handling se quisermos.
    # Já adicionamos no Passo 6.