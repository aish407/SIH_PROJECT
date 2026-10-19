$workspace = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $workspace
$env:PYTHONPATH = "$workspace\work\.venv\Lib\site-packages"
$env:PORT = if ($env:PORT) { $env:PORT } else { "8004" }
$python = "C:\Program Files\Python314\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
    throw "Python 3.14 was not found at $python. Install Python or update start-dashboard.ps1 with your Python path."
}
& $python -u "$workspace\scripts\run_roadwatch.py"
