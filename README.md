# 🩺 botCDS_v2-ESUS

Automação inteligente para preenchimento de fichas no sistema e-SUS AB (CDS), utilizando Playwright com Python assíncrono. O bot simula um profissional digitando dados de atendimentos clínicos, garantindo precisão e agilidade no processo de registro.

## ⚙️ Tecnologias Utilizadas

- 🐍 Python 3.11+
- 🎭 [Playwright](https://playwright.dev/python/)
- ⌨️ Automação de browser headless (com suporte a iframes)
- 🧩 Estrutura modular e extensível
- 🧠 Logging inteligente com contexto

## 🖥️ Funcionalidades

- Preenchimento automático de campos no e-SUS (Ficha de Atendimento Individual)
- Suporte a múltiplos tipos de atendimentos (diabetes, hipertensão etc.)
- Simulação de digitação humana (`_safe_fill_simule`)
- Seleção de códigos SIGTAP com inteligência
- Tratamento de pop-ups e erros do sistema
- Módulo reutilizável para novos tipos de ficha

## 📁 Estrutura do Projeto

```bash
.
├── app
│   ├── automation
│   │   ├── pages
│   │   │   └── procedimento_form.py
│   │   └── tasks
│   │       ├── base_task.py
│   │       └── proce_diabetes_task.py
│   └── core
│       └── errors.py
├── main.py
├── requirements.txt
└── README.md
```

## ▶️ Como executar

1. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   playwright install
   ```

2. Execute o bot:
   ```bash
   python main.py
   ```

## 📦 Como compilar para `.exe` (Windows)

Use o [PyInstaller](https://pyinstaller.org/):

```bash
pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed main.py
```

O executável estará em:
```
dist/main.exe
```

💡 Para publicar no GitHub:
- Crie uma pasta `release/`
- Mova o `.exe` para lá
- No GitHub, clique em `Releases > Draft new release`
- Faça o upload do `.exe`

# botcds.spec
# Execute com: pyinstaller botcds.spec

from PyInstaller.utils.hooks import collect_submodules
hidden_imports = collect_submodules('app')

block_cipher = None

a = Analysis(
    ['app/ui/main_window.py'],  # arquivo principal (ajuste se necessário)
    pathex=[],
    binaries=[],
    datas=[
        ('app/assets/*', 'assets'),  # Inclui assets (ícones, imagens)
        ('config/*.json', 'config'), # Configurações externas
    ],
    hiddenimports=hidden_imports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='botCDS',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Defina como False para esconder o terminal
    icon='app/assets/icon.ico',  # ✅ Ícone do executável
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='botCDS'
)
```

## 🧩 Adicionando novas tarefas? Veja a Wiki

## 📄 Licença

MIT. Sinta-se livre para contribuir, modificar ou utilizar.
