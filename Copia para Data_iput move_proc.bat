@echo off
setlocal enabledelayedexpansion

:: Caminho da pasta onde o .bat está (data_input)
set DATA_INPUT_DIR=%~dp0

:: Subpastas
set ARQUIVOS_DIR=%DATA_INPUT_DIR%arquivos
set PROCESSADOS_DIR=%DATA_INPUT_DIR%arquivos_processados

:: Verifica se a pasta "arquivos" existe
if not exist "%ARQUIVOS_DIR%" (
    echo [ERRO] Pasta "arquivos" nao encontrada.
    pause
    exit /b
)

:: Verifica se a pasta "arquivos_processados" existe
if not exist "%PROCESSADOS_DIR%" (
    echo [ERRO] Pasta "arquivos_processados" nao encontrada.
    pause
    exit /b
)

echo [INFO] Apagando arquivos .json da pasta arquivos...
del /Q "%ARQUIVOS_DIR%\*.json" >nul 2>&1

echo [INFO] Movendo arquivos dados*.csv de arquivos_processados...

:: Loop por todos os arquivos dados*.csv dentro de arquivos_processados
for %%F in ("%PROCESSADOS_DIR%\dados*.csv") do (
    set "FILE=%%~nxF"

    :: Verifica se é exatamente dados.csv
    if /I "!FILE!"=="dados.csv" (
        echo [INFO] Movendo !FILE! para data_input\
        move /Y "%%F" "%DATA_INPUT_DIR%\dados.csv" >nul
    ) else (
        echo [INFO] Movendo !FILE! para subpasta arquivos\
        move /Y "%%F" "%ARQUIVOS_DIR%\!FILE!" >nul
    )
)

echo [SUCESSO] Processamento finalizado.
pause
