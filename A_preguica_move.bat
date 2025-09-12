@echo off
setlocal enabledelayedexpansion

:: CONFIGURAÇÃO DO USUÁRIO
:: Defina aqui a quantidade de arquivos "dadosX.csv"
set Qtd_dados=21

:: CAMINHO DO SCRIPT (a raiz do projeto onde o .bat está)
set ROOT_DIR=%~dp0

:: Verifica se a pasta "resources" existe
if not exist "%ROOT_DIR%resources" (
    echo [ERRO] Pasta "resources" nao encontrada no caminho: %ROOT_DIR%
    pause
    exit /b
)

:: Verifica se a subpasta "resources\config" existe, senão cria
if not exist "%ROOT_DIR%resources\config" (
    mkdir "%ROOT_DIR%resources\config"
)

:: Verifica se a subpasta "resources\data_input" existe, senão cria
if not exist "%ROOT_DIR%resources\data_input" (
    mkdir "%ROOT_DIR%resources\data_input"
)

:: Verifica se a subpasta "resources\data_input\arquivos" existe, senão cria
if not exist "%ROOT_DIR%resources\data_input\arquivos" (
    mkdir "%ROOT_DIR%resources\data_input\arquivos"
)

echo [INFO] Procurando arquivo de configuracao...

:: Procura o arquivo que começa com "configuracao" e termina com ".csv"
for %%F in ("%ROOT_DIR%configuracao*.csv") do (
    echo [INFO] Encontrado: %%~nxF
    echo [INFO] Renomeando para configuracao.csv e movendo para resources\config
    move /Y "%%F" "%ROOT_DIR%resources\config\configuracao.csv"
    goto :proximo
)

:proximo
echo [INFO] Movendo arquivos dadosX.csv...

:: Loop de 1 até Qtd_dados
for /L %%i in (1,1,%Qtd_dados%) do (
    set "FILENAME=dados%%i.csv"
    if exist "!FILENAME!" (
        if %%i==1 (
            echo [INFO] Movendo e renomeando !FILENAME! para resources\data_input\dados.csv
            move /Y "!FILENAME!" "%ROOT_DIR%resources\data_input\dados.csv"
        ) else (
            echo [INFO] Movendo !FILENAME! para resources\data_input\arquivos\
            move /Y "!FILENAME!" "%ROOT_DIR%resources\data_input\arquivos\!FILENAME!"
        )
    ) else (
        echo [AVISO] Arquivo !FILENAME! nao encontrado.
    )
)

echo [SUCESSO] Todos os arquivos foram processados.
pause
