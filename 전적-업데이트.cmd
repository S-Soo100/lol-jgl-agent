@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo == LoL Jungle: 최근 5판 수집 + 자동분석 + 대시보드 ==
echo.
"%~dp0.venv\Scripts\python.exe" -m lol_jgl_agent.cli --count 5 --insights --dashboard --open
echo.
echo (Riot 키가 만료됐으면 .env의 RIOT_API_KEY를 갱신하세요)
pause
