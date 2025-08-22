# Arquivo: app/core/errors.py
class AutomationError(Exception):
    """Exceção base para erros de automação."""
    def __init__(self, message, step=None, data=None, screenshot_path=None, html_content=None):
        super().__init__(message)
        self.message = message
        self.step = step # Descrição do passo que falhou (e.g., "Clicar botão Confirmar")
        self.data = data # Dados da linha do CSV sendo processada no momento do erro
        self.screenshot_path = screenshot_path # Caminho para o screenshot
        self.html_content = html_content # HTML da página no momento do erro (opcional, pode ser grande)

    def __str__(self):
        details = f"Erro durante a automação: {self.message}"
        if self.step:
            details += f"\nPasso falhou: {self.step}"
        if self.data:
            # Exemplo: mostrar CPF/CNS ou algum identificador da linha de dados
            try:
                 details += f"\nDados (CPF/CNS): {self.data[1] if len(self.data) > 1 else 'N/A'}"
            except IndexError:
                 details += f"\nDados da linha: {self.data}" # Mostrar a linha inteira se não conseguir pegar o CPF
        if self.screenshot_path:
             details += f"\nScreenshot salvo em: {self.screenshot_path}"
        # Não incluir o HTML por padrão para não poluir o log/mensagem de erro

        return details

class ElementNotFoundError(AutomationError):
    """Erro quando um elemento esperado não é encontrado na página."""
    pass

class ElementNotInteractableError(AutomationError):
    """Erro quando um elemento é encontrado, mas não pode ser clicado ou preenchido."""
    pass

# Adicione outros tipos de erro específicos conforme precisar
# class LoginFailedError(AutomationError): pass
# class InvalidDataError(AutomationError): pass