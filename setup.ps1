#Requires -Version 5.1

param(
    [switch]$NonInteractive
)

$REQUIRED_PYTHON_MAJOR = 3
$REQUIRED_PYTHON_MINOR = 11
$VENV_DIR = ".venv"
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONUTF8 = "1"

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "--------------------------------------------------" -ForegroundColor Cyan
    Write-Host "  $Message" -ForegroundColor Cyan
    Write-Host "--------------------------------------------------" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "  [OK] $Message" -ForegroundColor Green
}

function Write-Info {
    param([string]$Message)
    Write-Host "  [INFO] $Message" -ForegroundColor Yellow
}

function Write-Err {
    param([string]$Message)
    Write-Host "  [ERROR] $Message" -ForegroundColor Red
}

function Pause-WithMessage {
    param([string]$Message = "Press any key to continue...")
    if ($NonInteractive) { return }
    Write-Host ""
    Write-Host $Message -ForegroundColor DarkGray
    try {
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    } catch {}
}

function Refresh-EnvironmentPath {
    $machinePath = [System.Environment]::GetEnvironmentVariable("Path", "Machine")
    $userPath = [System.Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path = "$machinePath;$userPath"
}

function Find-PythonCommand {
    Refresh-EnvironmentPath

    $py3 = Get-Command python3 -ErrorAction SilentlyContinue
    if ($py3) {
        $ver = & python3 --version 2>&1
        if ($ver -match "Python (\d+)\.(\d+)") {
            if ([int]$Matches[1] -ge $REQUIRED_PYTHON_MAJOR -and [int]$Matches[2] -ge $REQUIRED_PYTHON_MINOR) {
                return @{ Command = "python3"; Version = $ver }
            }
        }
    }

    $py = Get-Command python -ErrorAction SilentlyContinue
    if ($py) {
        $ver = & python --version 2>&1
        if ($ver -match "Python (\d+)\.(\d+)") {
            if ([int]$Matches[1] -ge $REQUIRED_PYTHON_MAJOR -and [int]$Matches[2] -ge $REQUIRED_PYTHON_MINOR) {
                return @{ Command = "python"; Version = $ver }
            }
        }
    }

    $pyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($pyLauncher) {
        $ver = & py -3 --version 2>&1
        if ($ver -match "Python (\d+)\.(\d+)") {
            if ([int]$Matches[1] -ge $REQUIRED_PYTHON_MAJOR -and [int]$Matches[2] -ge $REQUIRED_PYTHON_MINOR) {
                return @{ Command = "py -3"; Version = $ver }
            }
        }
    }

    return $null
}

Clear-Host
Write-Host ""
Write-Host "==================================================" -ForegroundColor Blue
Write-Host "   Multi-Agent AI Design Course Environment Setup   " -ForegroundColor Blue
Write-Host "==================================================" -ForegroundColor Blue
Write-Host ""

Write-Step "STEP 1: Checking Python Version & Auto Installation"

$pyResult = Find-PythonCommand

if ($null -eq $pyResult) {
    Write-Info "Python 3.11+ was not found. Starting automatic installation..."

    $installed = $false
    $wingetCmd = Get-Command winget -ErrorAction SilentlyContinue

    if ($wingetCmd) {
        Write-Info "Installing Python 3.11 using winget (user scope)..."
        & winget install --id Python.Python.3.11 --exact --silent --scope user --accept-package-agreements --accept-source-agreements
        if ($LASTEXITCODE -eq 0) {
            $installed = $true
            Write-Success "Python 3.11 installed via winget."
        }
    }

    if (-not $installed) {
        Write-Info "Downloading official Python installer..."
        $installerUrl = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
        $installerPath = Join-Path $env:TEMP "python-3.11.9-amd64.exe"

        try {
            Invoke-WebRequest -Uri $installerUrl -OutFile $installerPath -UseBasicParsing
            Write-Info "Installing Python 3.11 silently for current user..."
            $process = Start-Process -FilePath $installerPath -ArgumentList "/quiet InstallAllUsers=0 PrependPath=1 Include_test=0 Include_launcher=0" -Wait -PassThru
            if ($process.ExitCode -eq 0) {
                $installed = $true
                Write-Success "Python 3.11 installed via official installer."
            } else {
                Write-Err "Installer exited with code: $($process.ExitCode)"
            }
            Remove-Item $installerPath -ErrorAction SilentlyContinue
        } catch {
            Write-Err "Failed to download/install Python."
        }
    }

    Refresh-EnvironmentPath
    $pyResult = Find-PythonCommand

    if ($null -eq $pyResult) {
        Write-Err "Could not detect Python after installation."
        Write-Host "Please manually install Python 3.11+ from https://www.python.org/downloads/ and check 'Add Python to PATH'." -ForegroundColor Yellow
        exit 1
    }
}

$pythonCmd = $pyResult.Command
$ver = $pyResult.Version
Write-Success "Python OK: $($pythonCmd -replace 'py -3', 'py') ($ver)"

Write-Step "STEP 2: Creating Virtual Environment (.venv)"

Set-Location $SCRIPT_DIR

if (Test-Path $VENV_DIR) {
    Write-Info "Virtual environment ($VENV_DIR) already exists."
} else {
    Write-Info "Creating virtual environment..."
    if ($pythonCmd -eq "py -3") {
        & py -3 -m venv $VENV_DIR
    } else {
        & $pythonCmd -m venv $VENV_DIR
    }
    if ($LASTEXITCODE -ne 0) {
        Write-Err "Failed to create virtual environment."
        exit 1
    }
    Write-Success "Created virtual environment: $VENV_DIR"
}

$activateScript = Join-Path $SCRIPT_DIR "$VENV_DIR\Scripts\Activate.ps1"
if (-not (Test-Path $activateScript)) {
    Write-Err "Activate.ps1 not found: $activateScript"
    exit 1
}

try {
    $currentPolicy = Get-ExecutionPolicy -Scope CurrentUser -ErrorAction SilentlyContinue
    if ($currentPolicy -eq "Restricted" -or $currentPolicy -eq "Undefined") {
        Write-Info "Setting PowerShell execution policy..."
        Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force -ErrorAction SilentlyContinue
    }
} catch {}

& $activateScript
Write-Success "Activated virtual environment."

Write-Step "STEP 3: Installing Required Packages"

$pipPath = Join-Path $SCRIPT_DIR "$VENV_DIR\Scripts\pip.exe"
$pyPath = Join-Path $SCRIPT_DIR "$VENV_DIR\Scripts\python.exe"

Write-Info "Upgrading pip..."
& $pyPath -m pip install --upgrade pip --quiet
Write-Success "pip upgraded."

$requirementsFile = Join-Path $SCRIPT_DIR "requirements.txt"
if (Test-Path $requirementsFile) {
    Write-Info "Installing packages from requirements.txt..."
    & $pyPath -m pip install -r $requirementsFile
    if ($LASTEXITCODE -ne 0) {
        Write-Err "Failed to install required packages."
        exit 1
    }
    Write-Success "Installed required packages."
} else {
    Write-Err "requirements.txt not found."
    exit 1
}

Write-Step "STEP 4: Google AI Studio API Key Setup"

$existingKey = [System.Environment]::GetEnvironmentVariable("GOOGLE_API_KEY", "User")
if (-not $existingKey) { $existingKey = $env:GOOGLE_API_KEY }

if ($existingKey -and $existingKey.Length -gt 15) {
    Write-Success "API Key is already configured."
} else {
    if ($NonInteractive) {
        Write-Info "Non-interactive mode: Skipping API key input prompt."
    } else {
        Write-Host ""
        Write-Host "Get your API key from https://aistudio.google.com/" -ForegroundColor Yellow
        Write-Host ""

        $apiKey = ""
        while ($true) {
            $apiKey = Read-Host "Enter your GOOGLE_API_KEY"
            $apiKey = $apiKey.Trim()

            if ($apiKey.Length -gt 15 -and $apiKey -notmatch "\s") {
                break
            } else {
                Write-Err "Invalid API Key format (Must be at least 15 characters without spaces)."
            }
        }

        [System.Environment]::SetEnvironmentVariable("GOOGLE_API_KEY", $apiKey, "User")
        $env:GOOGLE_API_KEY = $apiKey

        Write-Success "Saved GOOGLE_API_KEY to user environment."
    }
}

if (-not $env:GOOGLE_API_KEY) {
    $env:GOOGLE_API_KEY = [System.Environment]::GetEnvironmentVariable("GOOGLE_API_KEY", "User")
}

Write-Step "STEP 5: Verification"

$verifyScript = Join-Path $SCRIPT_DIR "verify_setup.py"

if (Test-Path $verifyScript) {
    Write-Info "Running verify_setup.py..."
    & $pyPath $verifyScript
} else {
    Write-Info "verify_setup.py not found. Running basic check..."
    $checkScript = @"
import sys
print(f"Python: {sys.version}")
try:
    import google.adk
    print(f"google-adk: OK")
except ImportError as e:
    print(f"google-adk: ERROR - {e}")
"@
    $checkScript | & $pyPath -
}

Write-Step "STEP 6: VS Code Extensions"

$codeCmd = $null
$cCmd = Get-Command code -ErrorAction SilentlyContinue
if ($cCmd) { $codeCmd = "code" }

if (-not $codeCmd) {
    Write-Info "VS Code (code command) not found. Skipping extension install."
} else {
    $extensionsFile = Join-Path $SCRIPT_DIR ".vscode\extensions.json"
    if (Test-Path $extensionsFile) {
        $json = Get-Content $extensionsFile -Raw | ConvertFrom-Json
        $extensions = $json.recommendations
        Write-Info "Installing $($extensions.Count) VS Code extensions..."
        foreach ($ext in $extensions) {
            Write-Info "Installing: $ext"
            & $codeCmd --install-extension $ext --force 2>&1 | Out-Null
            if ($LASTEXITCODE -eq 0) {
                Write-Success "Installed: $ext"
            } else {
                Write-Info "Skipped or already installed: $ext"
            }
        }
        Write-Success "VS Code extensions installation complete."
    } else {
        Write-Info ".vscode\extensions.json not found."
    }
}

Write-Host ""
Write-Host "==================================================" -ForegroundColor Green
Write-Host "       Setup Completed Successfully!              " -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host ""
