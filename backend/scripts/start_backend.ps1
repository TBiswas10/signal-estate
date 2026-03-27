param(
    [int]$PreferredPort = 8000,
    [switch]$Reload = $true
)

$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $root

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
}

function Get-FreePort([int]$port) {
    $inUse = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { $_.LocalPort -eq $port }
    if ($inUse) {
        return $false
    }
    return $true
}

$port = $PreferredPort
while (-not (Get-FreePort $port)) {
    $port += 1
}

$venvPython = Join-Path $root ".venv/Scripts/python.exe"
$python = if (Test-Path $venvPython) { $venvPython } else { "python" }
$args = @("-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", "$port")
if ($Reload) {
    $args += "--reload"
}

Write-Host "Starting backend on http://127.0.0.1:$port"
Write-Host "Using Python: $python"
& $python @args
