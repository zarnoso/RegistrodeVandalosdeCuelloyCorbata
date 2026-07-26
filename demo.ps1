$ErrorActionPreference = "Stop"

$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$demoVenv = Join-Path $projectDir ".demo-venv"
$demoPython = Join-Path $demoVenv "Scripts\python.exe"

if (-not (Test-Path -LiteralPath $demoPython)) {
    Write-Host "Preparando entorno de la demo..."
    python -m venv $demoVenv
    & $demoPython -m pip install --quiet --upgrade pip
    & $demoPython -m pip install --quiet -r (Join-Path $projectDir "requirements-demo.txt")
}

Write-Host "Iniciando Trama Publica en http://127.0.0.1:8000"
& $demoPython (Join-Path $projectDir "scripts\run_demo.py")
