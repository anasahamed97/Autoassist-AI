@echo off
title AutoAssist AI - Automotive Diagnostic Intelligence Server
echo ========================================================
echo  AutoAssist AI: Starting Web Platform and API on Port 8000
echo ========================================================
echo  Web Dashboard : http://127.0.0.1:8000/
echo  Interactive Docs: http://127.0.0.1:8000/docs
echo ========================================================
set "PATH=C:\Users\anasa\anaconda3;C:\Users\anasa\anaconda3\Scripts;C:\Users\anasa\anaconda3\Library\bin;%PATH%"

:: Open default browser after 2 seconds
start "" cmd /c "timeout /t 2 /nobreak >nul & start http://127.0.0.1:8000/"

"C:\Users\anasa\anaconda3\python.exe" -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
pause
