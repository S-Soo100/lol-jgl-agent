@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo == 대시보드 열기 (Riot 수집 없음, 즉시) ==
"%~dp0.venv\Scripts\python.exe" -m lol_jgl_agent.cli --no-collect --dashboard --open
pause
