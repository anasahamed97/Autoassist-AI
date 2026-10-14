@echo off
title AutoAssist AI - Backend Server
echo ========================================================
echo  AutoAssist AI: Starting FastAPI Backend on Port 8000
echo ========================================================
set "PATH=C:\Users\anasa\anaconda3;C:\Users\anasa\anaconda3\Scripts;C:\Users\anasa\anaconda3\Library\bin;%PATH%"
"C:\Users\anasa\anaconda3\python.exe" -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
pause
