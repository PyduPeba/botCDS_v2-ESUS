@echo off
REM Arquivo batch para criar a estrutura no diretório atual

set "ROOT_DIR=%~dp0"
echo Criando estrutura em: %ROOT_DIR%

REM Criando diretórios principais
mkdir "%ROOT_DIR%app"
mkdir "%ROOT_DIR%app\core"
mkdir "%ROOT_DIR%app\data"
mkdir "%ROOT_DIR%app\automation"
mkdir "%ROOT_DIR%app\automation\pages"
mkdir "%ROOT_DIR%app\automation\tasks"
mkdir "%ROOT_DIR%app\gui"
mkdir "%ROOT_DIR%resources"
mkdir "%ROOT_DIR%resources\config"
mkdir "%ROOT_DIR%resources\data_input"
mkdir "%ROOT_DIR%resources\data_input\arquivos"
mkdir "%ROOT_DIR%resources\img"

REM Criando arquivos __init__.py
type nul > "%ROOT_DIR%app\__init__.py"
type nul > "%ROOT_DIR%app\core\__init__.py"
type nul > "%ROOT_DIR%app\data\__init__.py"
type nul > "%ROOT_DIR%app\automation\__init__.py"
type nul > "%ROOT_DIR%app\automation\pages\__init__.py"
type nul > "%ROOT_DIR%app\automation\tasks\__init__.py"
type nul > "%ROOT_DIR%app\gui\__init__.py"

REM Criando arquivos Python
type nul > "%ROOT_DIR%app\core\app_config.py"
type nul > "%ROOT_DIR%app\core\logger.py"
type nul > "%ROOT_DIR%app\core\errors.py"
type nul > "%ROOT_DIR%app\data\config_loader.py"
type nul > "%ROOT_DIR%app\data\file_manager.py"
type nul > "%ROOT_DIR%app\data\date_sequencer.py"
type nul > "%ROOT_DIR%app\automation\browser.py"
type nul > "%ROOT_DIR%app\automation\error_handler.py"
type nul > "%ROOT_DIR%app\automation\pages\base_page.py"
type nul > "%ROOT_DIR%app\automation\pages\login_page.py"
type nul > "%ROOT_DIR%app\automation\pages\main_menu.py"
type nul > "%ROOT_DIR%app\automation\pages\common_forms.py"
type nul > "%ROOT_DIR%app\automation\pages\atendimento_form.py"
type nul > "%ROOT_DIR%app\automation\pages\procedimento_form.py"
type nul > "%ROOT_DIR%app\automation\tasks\base_task.py"
type nul > "%ROOT_DIR%app\automation\tasks\atend_a97_task.py"
type nul > "%ROOT_DIR%app\automation\tasks\atend_diabetico_task.py"
type nul > "%ROOT_DIR%app\automation\tasks\atend_hipertenso_task.py"
type nul > "%ROOT_DIR%app\automation\tasks\atend_saude_repro_task.py"
type nul > "%ROOT_DIR%app\automation\tasks\proce_afericao_task.py"
type nul > "%ROOT_DIR%app\automation\tasks\proce_saude_repro_task.py"
type nul > "%ROOT_DIR%app\automation\tasks\hipertenso_procedimento_task.py"
type nul > "%ROOT_DIR%app\gui\main_window.py"
type nul > "%ROOT_DIR%app\gui\worker.py"
type nul > "%ROOT_DIR%app\gui\dialogs.py"
type nul > "%ROOT_DIR%main.py"

REM Criando arquivos de recursos
type nul > "%ROOT_DIR%resources\config\configuracao.csv"
type nul > "%ROOT_DIR%resources\config\config.json"
type nul > "%ROOT_DIR%resources\data_input\data.csv"
type nul > "%ROOT_DIR%resources\data_input\dados.csv"
type nul > "%ROOT_DIR%resources\data_input\arquivos\dataseqregistro.json"
type nul > "%ROOT_DIR%resources\img\Auto-py-to-exe.png"
type nul > "%ROOT_DIR%resources\img\capa.png"
type nul > "%ROOT_DIR%resources\img\icone.ico"

REM Criando requirements.txt
type nul > "%ROOT_DIR%requirements.txt"

echo Estrutura criada com sucesso em: %ROOT_DIR%
pause