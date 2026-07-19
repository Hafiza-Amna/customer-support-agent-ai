@echo off
REM ============================================================
REM  Customer Support Agent AI — Local Development Server
REM  Starts the ADK web UI at http://127.0.0.1:8001/dev-ui
REM ============================================================

echo.
echo  Starting Customer Support Agent AI...
echo  ADK Dev UI will be available at: http://127.0.0.1:8001/dev-ui
echo.

uv run python -m google.adk.cli web . --host 127.0.0.1 --port 8001

pause
