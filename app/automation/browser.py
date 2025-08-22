# Arquivo: app/automation/browser.py
from playwright.async_api import async_playwright, BrowserContext, Page, Browser
from app.core.logger import logger
from app.core.errors import AutomationError

class BrowserManager:
    """
    Gerencia a instância do navegador Playwright e o contexto de navegação.
    """
    def __init__(self):
        self._playwright = None
        self._browser: Browser = None
        self._context: BrowserContext = None
        self._page: Page = None

    async def launch_browser(self, headless=False) -> Page:
        """
        Inicia o navegador Playwright e cria um novo contexto e página.
        Retorna a instância da página.
        """
        logger.info(f"Lançando navegador Playwright (headless={headless})...")
        try:
            self._playwright = await async_playwright().start()
            # Use 'chromium' para Chrome, 'firefox', ou 'webkit' para Safari
            self._browser = await self._playwright.chromium.launch(headless=headless)
            self._context = await self._browser.new_context()

            # Adicione opções de contexto se precisar (ex: permissões, user agent)
            # self._context = await self._browser.new_context(permissions=['clipboard-read', 'clipboard-write'])

            self._page = await self._context.new_page()

            # Adicione um listener para erros no console do navegador (opcional)
            self._page.on("console", lambda msg: logger.debug(f"Browser console [{msg.type}]: {msg.text}"))

            logger.info("Navegador e página criados com sucesso.")
            return self._page
        except Exception as e:
            logger.critical(f"Erro ao iniciar o navegador Playwright: {e}")
            raise AutomationError(f"Falha ao iniciar o navegador: {e}") # Levanta uma exceção personalizada

    async def close_browser(self):
        """Fecha o navegador e o contexto Playwright."""
        if self._browser:
            logger.info("Fechando navegador Playwright...")
            try:
                await self._browser.close()
                self._browser = None
                self._context = None
                self._page = None
                logger.info("Navegador fechado.")
            except Exception as e:
                logger.error(f"Erro ao fechar o navegador Playwright: {e}")

        if self._playwright:
            logger.info("Parando Playwright...")
            try:
                await self._playwright.stop()
                self._playwright = None
                logger.info("Playwright parado.")
            except Exception as e:
                 logger.error(f"Erro ao parar Playwright: {e}")


# Exemplo de uso (somente para teste do módulo)
# if __name__ == '__main__':
#     import asyncio

#     async def test_browser():
#         manager = BrowserManager()
#         try:
#             page = await manager.launch_browser(headless=False) # Mude para True para não abrir a janela
#             await page.goto("https://playwright.dev")
#             logger.info(f"Página atual: {page.url}")
#             await asyncio.sleep(3) # Espera um pouco para ver a página
#         except AutomationError as e:
#             logger.error(f"Teste falhou: {e}")
#         finally:
#             await manager.close_browser()

#     asyncio.run(test_browser())