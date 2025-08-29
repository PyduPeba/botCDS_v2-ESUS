import os
import fnmatch

# Diretórios que nunca devem aparecer
IGNORAR_FIXO = {
    ".git", ".svn", ".hg", ".idea", ".vscode",
    "__pycache__", "hooks", "objects", "refs", "logs"
}

def carregar_gitignore(caminho_gitignore):
    """Carrega padrões do .gitignore"""
    padroes = []
    if os.path.exists(caminho_gitignore):
        with open(caminho_gitignore, "r", encoding="utf-8") as f:
            for linha in f:
                linha = linha.strip()
                if linha and not linha.startswith("#"):
                    padroes.append(linha.rstrip("/"))  # remove / no final
    # padrões comuns
    padroes += ["*.pyc", "*.pyo", "*.pyd", ".DS_Store"]
    return set(padroes)

def ignorar(caminho_rel, padroes):
    """Verifica se o caminho deve ser ignorado"""
    nome = os.path.basename(caminho_rel)

    # ignora se estiver na lista fixa
    if nome in IGNORAR_FIXO:
        return True

    # ignora se casar com o .gitignore
    for padrao in padroes:
        if fnmatch.fnmatch(caminho_rel, padrao) or fnmatch.fnmatch(nome, padrao):
            return True

    return False

def listar_estrutura(raiz, padroes, prefixo="", saida=None, raiz_base=None):
    """Lista recursivamente a estrutura do projeto"""
    if raiz_base is None:
        raiz_base = raiz

    try:
        itens = sorted(os.listdir(raiz))
    except PermissionError:
        return
    
    for i, item in enumerate(itens):
        caminho = os.path.join(raiz, item)
        caminho_rel = os.path.relpath(caminho, raiz_base)
        marcador = "└── " if i == len(itens) - 1 else "├── "

        if ignorar(caminho_rel, padroes):
            continue

        linha = prefixo + marcador + item
        print(linha)
        if saida:
            saida.write(linha + "\n")

        if os.path.isdir(caminho):
            novo_prefixo = prefixo + ("    " if i == len(itens) - 1 else "│   ")
            listar_estrutura(caminho, padroes, novo_prefixo, saida, raiz_base)

if __name__ == "__main__":
    raiz_projeto = os.path.dirname(os.path.abspath(__file__))
    caminho_gitignore = os.path.join(raiz_projeto, ".gitignore")
    padroes = carregar_gitignore(caminho_gitignore)

    arquivo_saida = os.path.join(raiz_projeto, "estrutura_projeto.txt")

    with open(arquivo_saida, "w", encoding="utf-8") as saida:
        cabecalho = "Estrutura do projeto:\n\n" + os.path.basename(raiz_projeto)
        print(cabecalho)
        saida.write(cabecalho + "\n")
        listar_estrutura(raiz_projeto, padroes, saida=saida)

    print(f"\n✅ Estrutura salva em {arquivo_saida}")
