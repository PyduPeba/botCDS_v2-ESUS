# Arquivo: app/automation/browser.py
from playwright.async_api import async_playwright, BrowserContext, Page, Browser
from app.core.logger import logger
from app.core.errors import AutomationError
from pathlib import Path
import asyncio

class BrowserManager:
    """
    Gerencia a instância do navegador Playwright e o contexto de navegação.
    """
    def __init__(self):
        self._playwright = None
        self._browser: Browser = None
        self._context: BrowserContext = None
        self._page: Page = None

    async def launch_browser(self, headless=False, enable_trace: bool = True, use_chrome: bool = False) -> Page:
        """
        Inicia o navegador Playwright e cria um novo contexto e página.
        Retorna a instância da página.
        """
        logger.info(f"Lançando navegador Playwright (headless={headless}, Chrome={use_chrome})...")
        try:
            self._playwright = await async_playwright().start()
            
            # --- Lógica Condicional para Chrome/Firefox ---
            if use_chrome:
                logger.info("Tentando lançar Google Chrome...")
                self._browser = await self._playwright.chromium.launch(headless=headless, channel="chrome")
            else:
                logger.info("Tentando lançar Mozilla Firefox (padrão)...")
                self._browser = await self._playwright.firefox.launch(headless=headless) # Usando Firefox por padrão
            self._context = await self._browser.new_context() # Contexto padrão sem vídeo

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
