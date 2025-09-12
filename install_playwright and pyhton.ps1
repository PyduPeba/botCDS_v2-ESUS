<# 
    install_playwright.ps1
    - Garante Python 3.13.2 instalado (se não existir)
    - Garante playwright==1.52.0
    - Instala browsers (chromium, firefox, webkit)
#>

param(
    [string]$PythonExe = "python"
)

$ErrorActionPreference = "Stop"
$targetVersion = "1.52.0"
$pythonVersion = "3.13.2"
$pythonInstaller = "python-$pythonVersion-amd64.exe"
$pythonUrl = "https://www.python.org/ftp/python/$pythonVersion/$pythonInstaller"

function ExitWithError($msg) {
    Write-Host "ERRO: $msg" -ForegroundColor Red
    exit 1
}

function Get-PythonVersion {
    try {
        $v = & $PythonExe -c "import sys; print(sys.version.split()[0])" 2>$null
        return $v
    } catch {
        return $null
    }
}

function Get-PlaywrightVersion {
    try {
        $v = & $PythonExe -c "import playwright; print(playwright.__version__)" 2>$null
        return $v
    } catch {
        return $null
    }
}

# 1) Checar Python
$pyVer = Get-PythonVersion
if (-not $pyVer) {
    Write-Host "Python não encontrado. Baixando e instalando Python $pythonVersion ..." -ForegroundColor Yellow
    $installerPath = Join-Path $env:TEMP $pythonInstaller

    # Baixar instalador
    Invoke-WebRequest -Uri $pythonUrl -OutFile $installerPath -UseBasicParsing

    # Instalar silenciosamente (all users + PATH)
    Start-Process -FilePath $installerPath -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1 Include_test=0" -Wait -NoNewWindow

    # Forçar refresh de PATH
    $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH","Machine")

    # Atualizar caminho do python
    $PythonExe = "python"
    $pyVer = Get-PythonVersion
    if (-not $pyVer) {
        ExitWithError "Falha ao instalar Python $pythonVersion. Instale manualmente."
    }
    Write-Host "Python $pyVer instalado com sucesso." -ForegroundColor Green
} else {
    Write-Host "Python detectado: $pyVer em '$PythonExe'." -ForegroundColor Cyan
}

# 2) Checar Playwright
$pwVer = Get-PlaywrightVersion
if ($pwVer) {
    Write-Host "Playwright detectado: versão $pwVer." -ForegroundColor Yellow
} else {
    Write-Host "Playwright não encontrado neste Python." -ForegroundColor Yellow
}

# 3) Instalar/atualizar Playwright se necessário
$ensureBrowsersOnly = $false
if ($pwVer -and ($pwVer -eq $targetVersion)) {
    Write-Host "Versão alvo ($targetVersion) já instalada. Pulando instalação do pacote." -ForegroundColor Green
    $ensureBrowsersOnly = $true
} else {
    Write-Host "Instalando/atualizando Playwright para $targetVersion ..." -ForegroundColor Cyan
    try {
        & $PythonExe -m pip install --upgrade pip
        & $PythonExe -m pip install "playwright==$targetVersion"
        Write-Host "Playwright $targetVersion instalado/atualizado com sucesso." -ForegroundColor Green
    } catch {
        ExitWithError "Falha ao instalar playwright==$targetVersion. Detalhes: $($_.Exception.Message)"
    }
}

# 4) Instalar browsers
Write-Host "Instalando browsers (chromium, firefox, webkit)..." -ForegroundColor Cyan
try {
    & $PythonExe -m playwright install chromium firefox webkit
    Write-Host "Browsers instalados/verificados com sucesso." -ForegroundColor Green
} catch {
    ExitWithError "Falha ao instalar os browsers do Playwright. Detalhes: $($_.Exception.Message)"
}

# 5) Resumo
if ($ensureBrowsersOnly) {
    Write-Host "Concluído: Playwright já estava em $targetVersion; apenas os browsers foram (re)instalados/verificados." -ForegroundColor Green
} else {
    Write-Host "Concluído: Python $pyVer, Playwright $targetVersion e browsers instalados." -ForegroundColor Green
}
