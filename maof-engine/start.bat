@echo off
cd /d %~dp0
echo.
echo  Maof Engine — starting...
echo  Docs: http://localhost:8000/docs
echo.
python -m uvicorn app:app --reload --port 8000
