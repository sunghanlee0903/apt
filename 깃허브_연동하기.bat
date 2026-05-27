@echo off
chcp 65001 > nul
echo ======================================================
echo           APT 실거래가 대시보드 GitHub 자동 연동기
echo ======================================================
echo.

:: 1. Git 설치 확인 및 설치
where git >nul 2>nul
if %errorlevel% neq 0 (
    echo [!] 시스템에 Git이 설치되어 있지 않습니다.
    echo [*] winget을 사용하여 Git 설치를 시작합니다...
    winget install --id Git.Git -e --source winget --accept-package-agreements --accept-source-agreements
    if %errorlevel% neq 0 (
        echo [ERROR] Git 설치에 실패했습니다. 관리자 권한으로 터미널을 열고 다시 시도해 주세요.
        pause
        exit /b %errorlevel%
    )
    echo [OK] Git 설치가 완료되었습니다!
    echo.
) else (
    echo [OK] Git이 이미 설치되어 있습니다.
)

:: 2. GitHub CLI 설치 확인 및 설치
where gh >nul 2>nul
if %errorlevel% neq 0 (
    echo [!] 시스템에 GitHub CLI (gh)가 설치되어 있지 않습니다.
    echo [*] winget을 사용하여 GitHub CLI 설치를 시작합니다...
    winget install --id GitHub.cli -e --source winget --accept-package-agreements --accept-source-agreements
    if %errorlevel% neq 0 (
        echo [ERROR] GitHub CLI 설치에 실패했습니다.
        pause
        exit /b %errorlevel%
    )
    echo [OK] GitHub CLI 설치가 완료되었습니다!
    echo.
) else (
    echo [OK] GitHub CLI가 이미 설치되어 있습니다.
)

:: Refresh Path to ensure git and gh commands are recognized
refreshenv >nul 2>nul
set "PATH=%PATH%;C:\Program Files\Git\cmd;C:\Program Files\GitHub CLI"

:: Check again
where git >nul 2>nul
if %errorlevel% neq 0 (
    echo [!] 환경 변수 반영을 위해 현재 창을 닫고, '깃허브_연동하기.bat'를 다시 실행해 주세요!
    pause
    exit /b 0
)

echo ======================================================
echo               GitHub 계정 로그인 (1회 필수)
echo ======================================================
echo [*] 아래 로그인 마법사에 따라 브라우저에서 로그인해 주세요.
echo [*] 가이드:
echo   1. 'What is your preferred protocol...' -> 'GitHub.com' 선택 (엔터)
echo   2. 'What is your preferred protocol for Git operations?' -> 'HTTPS' 선택 (엔터)
echo   3. 'Authenticate Git with your GitHub credentials?' -> 'Yes' 선택 (엔터)
echo   4. 'How would you like to authenticate GitHub CLI?' -> 'Login with a web browser' 선택 (엔터)
echo   5. 'one-time code: XXXX-XXXX' 가 화면에 뜨면, 엔터를 눌러 웹 브라우저를 엽니다.
echo   6. 브라우저 창에 복사된 코드를 붙여넣고 'Authorize github'를 클릭하여 로그인을 승인합니다.
echo ======================================================
echo.
pause

call gh auth login
if %errorlevel% neq 0 (
    echo [ERROR] GitHub 로그인에 실패했거나 취소되었습니다.
    pause
    exit /b %errorlevel%
)

echo.
echo [OK] GitHub 로그인 성공!
echo.
echo ======================================================
echo          로컬 저장소 초기화 및 원격 'apt' 생성/푸시
echo ======================================================

:: Initialize Git locally
if not exist .git (
    git init
)

:: Stage and commit files (.gitignore에 의해 .env 등 핵심 키는 자동 보호됩니다)
git add .
git commit -m "feat: Soothing Sage theme revamp and open map layout complete"

:: Change branch to main
git branch -M main

:: Create repository 'apt' on GitHub and Push locally in one shot!
echo [*] GitHub에 'apt' 이름으로 저장소를 생성하고 코드를 푸시합니다...
call gh repo create apt --public --source=. --remote=origin --push

if %errorlevel% neq 0 (
    echo [!] 저장소가 이미 존재하거나 푸시 중 오류가 발생했습니다.
    echo [*] 이미 저장소가 존재한다면 기존 연결을 시도합니다...
    git remote remove origin >nul 2>nul
    gh repo view apt >nul 2>nul
    if %errorlevel% eq 0 (
        :: Repo exists, link it
        for /f "tokens=*" %%i in ('gh repo view apt --json url -q .url') do set REPO_URL=%%i
        git remote add origin %REPO_URL%
        git push -u origin main
    ) else (
        echo [ERROR] 작업에 실패했습니다. 오류 메시지를 확인해 주세요.
    )
)

echo.
echo ======================================================
echo 🎉 축하합니다! GitHub 'apt' 저장소 연동 및 푸시가 완료되었습니다!
echo ======================================================
pause
