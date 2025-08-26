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

## 🧩 Adicionando novas tarefas? Veja a Wiki

## 📄 Licença

MIT. Sinta-se livre para contribuir, modificar ou utilizar.