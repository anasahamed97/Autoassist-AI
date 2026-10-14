@echo off
title AutoAssist AI - Benchmark Evaluation
echo ========================================================
echo  AutoAssist AI: Running 16-Query Retrieval Benchmark
echo ========================================================
set "PATH=C:\Users\anasa\anaconda3;C:\Users\anasa\anaconda3\Scripts;C:\Users\anasa\anaconda3\Library\bin;%PATH%"
"C:\Users\anasa\anaconda3\python.exe" scripts\evaluate_retrieval.py
echo.
pause
