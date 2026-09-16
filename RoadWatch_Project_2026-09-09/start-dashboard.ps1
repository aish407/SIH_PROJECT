$workspace = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $workspace
& "$workspace\work\.venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000
