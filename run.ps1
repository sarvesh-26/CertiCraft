if (-not (Test-Path .venv)) {
    Write-Host "Creating virtual environment..."
    py -m venv .venv
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
. .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
uvicorn app.main:app --reload
