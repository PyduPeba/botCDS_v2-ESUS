# Arquivo: app/automation/browser.py
from playwright.async_api import async_playwright, BrowserContext, Page, Browser, Playwright # Import Playwright para type hint
from app.core.logger import logger
from app.core.errors import AutomationError
from pathlib import Path
import asyncio
import os # Importar os para manipulação de variáveis de ambiente

class BrowserManager:
    """
    Gerencia a instância do navegador Playwright e o contexto de navegação.
    """
    def __init__(self):
        self._playwright: Playwright = None # Adicionado type hint para clareza
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
            
            browser_type = None
            browser_name_for_log = ""
            
            if use_chrome:
                browser_type = self._playwright.chromium
                browser_name_for_log = "Google Chrome"
            else:
                browser_type = self._playwright.firefox
                browser_name_for_log = "Mozilla Firefox"
            
        
            logger.info(f"Tentando lançar {browser_name_for_log}...")

            # --- MODIFICAÇÃO CHAVE: Chamar launch() SEM 'executable_path' ---
            # O Playwright irá procurar o executável em:
            # 1. PLAYWRIGHT_BROWSERS_PATH (se definido, ideal para produção)
            # 2. Local padrão relativo ao pacote Playwright (ideal para desenvolvimento)
            
            # Se você usa 'channel="chrome"' para Chromium, mantenha-o APENAS para Chromium.
            # Para Firefox, não há 'channel' equivalente para instalações padrão.
            if use_chrome:
                self._browser = await browser_type.launch(
                    headless=headless, 
                    channel="chrome" # Use channel="chrome" para Chromium se quiser uma instalação estável do Chrome no sistema
                )
            else:
                self._browser = await browser_type.launch(
                    headless=headless
                )
           

            self._context = await self._browser.new_context() # Contexto padrão sem vídeo

            self._page = await self._context.new_page()

            # Adicione um listener para erros no console do navegador (opcional)
            self._page.on("console", lambda msg: logger.debug(f"Browser console [{msg.type}]: {msg.text}"))

            logger.info("Navegador e página criados com sucesso.")
            return self._page
        except Exception as e:
            logger.critical(f"Erro ao iniciar o navegador Playwright: {e}", exc_info=True)
            # A mensagem de erro pode ser genérica agora, mas a causa raiz ainda será
            # que o navegador não foi encontrado ou não pôde ser iniciado.
            # A instrução para o usuário ainda é válida.
            raise AutomationError(f"Falha ao iniciar o navegador: O navegador {browser_name_for_log} não pôde ser iniciado. "
                                  "Verifique se 'playwright install' foi executado no ambiente de produção "
                                  "e se a variável de ambiente PLAYWRIGHT_BROWSERS_PATH aponta para o diretório correto (normalmente AppData\\Local\\ms-playwright). "
                                  "Se estiver usando Chrome e tiver problemas, tente desmarcar 'Usar Navegador Chrome' para usar Firefox.") from e
        

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