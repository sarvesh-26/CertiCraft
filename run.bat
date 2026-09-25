@echo off
if not exist .venv (
  echo Creating virtual environment...
  py -m venv .venv || exit /b 1
)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
if not exist .env copy .env.example .env >nul
uvicorn app.main:app --reload
