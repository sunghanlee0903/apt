@echo off
title Apartment Transaction Analyzer Launcher
echo =================================================================
echo        APT Price Analyzer - Premium Dashboard Launcher
echo =================================================================
echo.
echo [1/3] FastAPI 웹 서버를 시작하는 중입니다...
echo.

:: Start python server in background
start /b python app.py

:: Bounded wait for server startup
timeout /t 2 >nul

echo [2/3] 서버 시작을 감지했습니다. 웹 브라우저를 구동합니다...
echo.

:: Open default web browser at local URL
start http://127.0.0.1:8000

echo [3/3] 브라우저 실행이 완료되었습니다!
echo.
echo =================================================================
echo   대시보드 구동 중... 서버를 종료하려면 이 창을 닫아주세요.
echo =================================================================
echo.
pause
