# Arquivo: app/core/utils.py
import unicodedata

def normalize_text_for_selection(text: str) -> str:
    """
    Remove acentos, caracteres especiais e converte para minúsculas
    para uso seguro em comparações de texto e seletores.
    """
    if not isinstance(text, str):
         # Retorna string vazia ou None se o input não for string.
         # String vazia é mais segura para usar em comparações normalized.
         return ""

    # Remove acentos (NFD) e caracteres combinados (ASCII), converte para minúsculas
    normalized = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode('utf-8').lower()
    return normalized