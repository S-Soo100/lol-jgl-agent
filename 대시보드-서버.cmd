@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo == 대시보드 서버 (페이지 안 '업데이트' 버튼) — 창을 닫거나 Ctrl+C로 종료 ==
"%~dp0.venv\Scripts\python.exe" -m lol_jgl_agent.serve
pause
