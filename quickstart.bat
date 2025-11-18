@echo off
REM Quick Start Guide for Distributed Key-Value Store (Windows)

echo.
echo ==========================================
echo Distributed Key-Value Store - Quick Start
echo ==========================================
echo.
echo This will help you start:
echo   1. Coordinator (port 5000)
echo   2. Nodes (ports 5001, 5002, 5003)
echo   3. Client
echo.
echo Prerequisites: Python 3.7+
echo.

pause

echo.
echo Starting Coordinator...
echo (Run this in a new Command Prompt, or add 'start' to background it)
echo.
echo   python coordinator/coordinator.py
echo.

pause

echo.
echo Starting Nodes...
echo (Run each in a new Command Prompt)
echo.
echo Command Prompt 1:
echo   python node/node.py 5001
echo.
echo Command Prompt 2:
echo   python node/node.py 5002
echo.
echo Command Prompt 3:
echo   python node/node.py 5003
echo.

pause

echo.
echo Starting Client...
echo.
echo Interactive mode (recommended for testing):
echo   python client/client.py
echo.
echo Or single command mode:
echo   python client/client.py --command "PUT key value"
echo.

set /p start_client="Start client? (y/n): "
if /i "%start_client%"=="y" (
    python client/client.py
)
