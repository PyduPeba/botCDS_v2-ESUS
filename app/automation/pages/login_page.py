# Arquivo: app/automation/pages/login_page.py (VERSÃO v3 - Lógica de Perfil Centralizada)
from playwright.async_api import Page, Locator
from app.automation.pages.base_page import BasePage
from app.core.logger import logger
from app.core.errors import AutomationError, ElementNotFoundError
# **ADICIONE OU VERIFIQUE ESTA IMPORTAÇÃO**
from app.automation.error_handler import AutomationErrorHandler
import asyncio 

class LoginPage(BasePage):
    """
    Representa a página de Login do sistema e-SUS.
    """
    # Seletores (Localizadores) - Usaremos seletores CSS ou XPath mais robustos que IDs genéricos
    # É fundamental inspecionar o site real para obter seletores confiáveis e menos propensos a mudar
    _URL_POPUP_COOKIES_BUTTON = 'button:has-text("Aceitar todos")' # Exemplo de seletor CSS para o botão de cookies
    _URL_CONTINUAR_BUTTON = 'button:has-text("Continuar")' # Exemplo de seletor CSS para o botão continuar pós-login

    # Seletor para o campo de usuário. Tente usar algo mais específico se possível.
    # Exemplo: input[placeholder="Usuário"], input[name="usuario"], input#login-username
    # Vamos usar o XPath do seu código original por enquanto, mas teste e refine!
    _USERNAME_FIELD_XPATH = '//*[@id="root"]/div/div[3]/div[1]/div/div[2]/div/form/div/div[1]/div/div[1]/div/div/input'
    # Seletor para o campo de senha
    _PASSWORD_FIELD_XPATH = '//*[@id="root"]/div/div[3]/div[1]/div/div[2]/div/form/div/div[2]/div/div/div/div[1]/div/div/input'
    # Seletor para o botão de login
    # _LOGIN_BUTTON_XPATH = '//*[@id="root"]/div/div[3]/div[1]/div/div[2]/div/form/div/div[3]/button'
    # Usando o data-cy sugerido na análise:
    _LOGIN_BUTTON_SELECTOR = '[data-cy="LoginForm.access-button"]'

    # Seletor para o cartão do perfil do enfermeiro (substitua pelo seletor correto no seu site)
    # No seu código antigo, você clicava em um div com número no final, o que é instável.
    # Vamos tentar encontrar pelo texto ou um atributo mais confiável.
    # Exemplo: div:has-text("Enfermeiro da estratégia de saúde da família")
    _ENFERMEIRO_CARD_SELECTOR = '[data-cy="Acesso.card"]:has-text("Enfermeiro da estratégia de saúde da família")' # Exemplo
    _UNIDADE_CARD_SELECTOR = '[data-cy="Acesso.card"]' # Seletor mais genérico para cartões de acesso, precisaremos escolher o correto

    # --- SELETORES PARA AMBAS AS TELAS DE PERFIL ---
    # Tela 1: Seleção por Cartões (NOVO)
    _PROFILE_CARD_SELECTOR_TEMPLATE = '[data-cy="Acesso.card"]:has-text("{}")'
    _UNIT_CARD_SELECTOR = '[data-cy="Acesso.card"]' # Pega o primeiro card de unidade

    # Tela 2: Seleção por Dropdowns (Antigo)
    _PROFILE_DROPDOWN_SELECTOR = 'div[peid="ocupacao-combo"]'
    _PROFILE_LIST_ITEM_SELECTOR_TEMPLATE = 'li.x-boundlist-item:has-text("{}")'
    _UNIDADE_DROPDOWN_SELECTOR = 'div[peid="unidade-saude-combo"]'
    _UNIDADE_LIST_ITEM_SELECTOR = 'li.x-boundlist-item'
    _CONFIRM_PROFILE_BUTTON_SELECTOR = 'button:has-text("Confirmar")'
    # --- FIM DOS SELETORES ---

    def __init__(self, page: Page, error_handler: AutomationErrorHandler):
        super().__init__(page, error_handler) # Inicializa a BasePage

    async def navigate_and_login(self, url: str, username: str, password: str):
        """Navega para a URL de login, lida com popups e realiza o login."""
        logger.info(f"Navegando para a URL: {url}")
        await self._safe_goto(url, step_description=f"Navegar para {url}")

        # Lidar com popup de cookies (se existir e aparecer rapidamente)
        # Usamos Locator.first.click() para clicar no primeiro elemento que corresponder
        # await self._page.locator(self._URL_POPUP_COOKIES_BUTTON).first.click() # Isso falhará se o elemento não estiver lá imediatamente
        # Uma abordagem mais segura: esperar um pouco por ele e clicar APENAS SE estiver visível
        logger.debug("Verificando popup de cookies...")
        try:
             cookie_button_locator = self._page.locator(self._URL_POPUP_COOKIES_BUTTON)
             # Espera um curto período, se o botão não aparecer, ignora
             await cookie_button_locator.wait_for(state="visible", timeout=5000) # Espera no máximo 5 segundos
             await self._safe_click(cookie_button_locator, "Botão 'Aceitar todos' (Cookies)")
             logger.info("Popup de cookies aceito.")
        except Exception: # Captura qualquer erro (TimeoutError se não aparecer, etc.)
             logger.debug("Popup de cookies não encontrado ou erro ao clicar.")
             # Continua mesmo que não tenha clicado no popup

        logger.info("Preenchendo credenciais de login...")
        # Preenche usuário e senha usando os métodos seguros da BasePage
        await self._safe_fill(
            self._page.locator(self._USERNAME_FIELD_XPATH),
            username,
            step_description="Campo Usuário"
        )
        await self._safe_fill(
            self._page.locator(self._PASSWORD_FIELD_XPATH),
            password,
            step_description="Campo Senha"
        )

        logger.info("Clicando no botão de Login...")
        # Clica no botão de login
        await self._safe_click(
            self._page.locator(self._LOGIN_BUTTON_SELECTOR),
            step_description="Botão Login"
        )

        # Aguardar carregamento pós-login (pode ser um redirecionamento ou aparecimento de um elemento na próxima página)
        # Pode ser necessário esperar por um elemento específico da página principal após o login
        # Exemplo: esperar por um elemento do menu ou um título
        # await self._page.wait_for_selector('seletor_de_algum_elemento_na_proxima_pagina', timeout=20000)
        await self._page.wait_for_load_state('domcontentloaded', timeout=20000) # Espera o DOM carregar

        # Lidar com popup "Continuar" pós-login (se existir)
        logger.debug("Verificando popup 'Continuar' pós-login...")
        try:
            continue_button_locator = self._page.locator(self._URL_CONTINUAR_BUTTON)
            await continue_button_locator.wait_for(state="visible", timeout=5000)
            await self._safe_click(continue_button_locator, "Botão 'Continuar' pós-login")
            logger.info("Popup 'Continuar' pós-login clicado.")
            await self._page.wait_for_load_state('domcontentloaded', timeout=10000) # Espera após clicar
        except Exception: # Captura TimeoutError se não aparecer ou erro ao clicar
            logger.debug("Popup 'Continuar' pós-login não encontrado ou erro ao clicar. Continuando.")


        # A lógica de seleção de perfil agora é responsabilidade exclusiva da BaseTask.
        logger.info("Login concluído. A tarefa continuará com a seleção de perfil, se necessário.")
        
    async def select_profile_and_unidade_optional(self, profile_name_to_select: str = "Enfermeiro") -> bool:
        """
        Função unificada e robusta para selecionar perfil e unidade na tela de cartões.
        Aceita o nome do perfil como argumento para ser flexível.
        """
        logger.info(f"Tentando selecionar o perfil via card: '{profile_name_to_select}'...")

        # Mapeia o nome curto para o texto completo no card
        profile_text_map = {
            "Enfermeiro": "Enfermeiro da estratégia de saúde da família",
            "AGENTE COMUNITARIO DE SAUDE": "Agente comunitário de saúde"
        }
        full_profile_text = profile_text_map.get(profile_name_to_select, profile_name_to_select)

        try:
            profile_locator = self._page.locator(self._PROFILE_CARD_SELECTOR_TEMPLATE.format(full_profile_text))
            await profile_locator.wait_for(state="visible", timeout=5000)
            
            await self._safe_click(profile_locator, f"Cartão '{full_profile_text}'")
            logger.info(f"Perfil '{full_profile_text}' selecionado com sucesso.")

            # Espera a navegação para a tela de unidades ser concluída
            logger.info("Aguardando a tela de seleção de unidade carregar...")
            await self._page.wait_for_load_state("networkidle", timeout=2000)

            logger.info("Selecionando a primeira unidade disponível...")
            unit_card_locator = self._page.locator(self._UNIT_CARD_SELECTOR).first
            await self._safe_click(unit_card_locator, "Primeiro cartão de Unidade disponível")
            
            await self._page.wait_for_load_state("networkidle", timeout=20000)
            logger.info("Unidade selecionada com sucesso.")
            return True

        except TimeoutError:
            logger.warning(f"Tela de seleção de perfil por card não encontrada para '{full_profile_text}'. A automação continuará.")
            return False
        except Exception as e:
            logger.error(f"Erro inesperado durante a seleção de perfil/unidade: {e}", exc_info=True)
            return False

    async def select_enfermeiro_and_unidade(self):
        """Seleciona o perfil de enfermeiro e clica na primeira unidade disponível."""
        logger.info("Selecionando perfil de Enfermeiro...")
        # Encontra o cartão do enfermeiro pelo texto e clica nele
        # A espera está dentro do _safe_click
        await self._safe_click(
            self._page.locator(self._ENFERMEIRO_CARD_SELECTOR),
            step_description="Cartão 'Enfermeiro da estratégia de saúde da família'"
        )

        # Aguardar carregamento após selecionar o perfil
        await self._page.wait_for_load_state('domcontentloaded', timeout=5000)

        logger.info("Selecionando unidade (primeira disponível)...")
        # Encontra TODOS os cartões de unidade genéricos
        unit_cards_locator = self._page.locator(self._UNIDADE_CARD_SELECTOR)
        # Pega o primeiro cartão de unidade visível e clica
        await self._safe_click(
            unit_cards_locator.first, # Pega o primeiro elemento que corresponde ao seletor
            step_description="Primeiro cartão de Unidade disponível"
        )
        # Aguardar carregamento após selecionar a unidade
        await self._page.wait_for_load_state('domcontentloaded', timeout=20000)
        logger.info("Unidade selecionada.")

# Exemplo de uso (requer Playwright e um site de teste ou o site real)
# if __name__ == '__main__':
#      import asyncio
#      from app.automation.browser import BrowserManager # Importa o BrowserManager real
#
#      async def test_login_flow():
#           browser_manager = BrowserManager()
#           page = None
#           try:
#                page = await browser_manager.launch_browser(headless=False)
#                # Para este teste, precisamos de um ErrorHandler. Podemos usar um mock simples.
#                class SimpleMockErrorHandler:
#                    async def handle_error(self, e, step_description=""):
#                        print(f"--- MOCK ERROR HANDLER --- Erro em '{step_description}': {e}")
#                        # Não pausa nem levanta exceções de controle para este teste simples
#                mock_handler = SimpleMockErrorHandler()
#
#                login_page = LoginPage(page, mock_handler)
#
#                # Use credenciais e URL de teste/desenvolvimento
#                TEST_URL = "SUA_URL_DE_TESTE_OU_DESENVOLVIMENTO" # <<< SUBSTITUA
#                TEST_USER = "SEU_USUARIO" # <<< SUBSTITUA
#                TEST_PASSWORD = "SUA_SENHA" # <<< SUBSTITUA
#
#                if TEST_URL == "SUA_URL_DE_TESTE_OU_DESENVOLVIMENTO":
#                     print("Por favor, configure TEST_URL, TEST_USER e TEST_PASSWORD para testar o login.")
#                     return
#
#                await login_page.navigate_and_login(TEST_URL, TEST_USER, TEST_PASSWORD)
#
#                # Após o login, simula a seleção de perfil/unidade (ajuste seletores se necessário)
#                # IMPORTANTE: Os seletores _ENFERMEIRO_CARD_SELECTOR e _UNIDADE_CARD_SELECTOR
#                # SÃO APENAS EXEMPLOS e PRECISAM ser verificados no site REAL!
#                # Pode ser necessário esperar por elementos na página pós-login antes de tentar selecionar perfil.
#                # await page.wait_for_selector('seletor_de_elemento_pos_login', timeout=10000) # Exemplo
#                await login_page.select_enfermeiro_and_unidade()
#
#                logger.info("Fluxo de login e seleção de perfil/unidade concluído com sucesso (simulado).")
#                await asyncio.sleep(5) # Deixa o navegador aberto por um tempo para você ver
#
#           except AutomationError as e:
#                logger.error(f"Falha na automação durante o teste de login: {e}")
#           except Exception as e:
#                logger.error(f"Erro inesperado durante o teste de login: {e}")
#           finally:
#                if browser_manager:
#                     await browser_manager.close_browser()
#
#      # asyncio.run(test_login_flow()) # Descomente para rodar o teste (configure as credenciais antes)