@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"
set REPO=vibe-z

echo == Initializing git repo ==
if not exist .git (
  git init
)

echo == Setting main branch ==
git branch -M main

echo == Adding files ==
git add .

echo == Creating commit (if needed) ==
git diff --cached --quiet
if errorlevel 1 (
  git rev-parse --verify HEAD >nul 2>nul
  if errorlevel 1 (
    git commit -m "Initial commit"
  ) else (
    git commit -m "Update"
  )
) else (
  echo (nothing to commit)
)

echo == GitHub auth ==
gh auth status >nul 2>nul
if errorlevel 1 (
  gh auth login
)

echo == Detecting GitHub user ==
for /f "delims=" %%i in ('gh api user --jq .login 2^>nul') do set GH_USER=%%i
if "%GH_USER%"=="" (
  echo Could not detect GitHub user. Are you logged in to gh?
  echo Run: gh auth login
  pause
  exit /b 1
)

echo == Creating repo if missing ==
gh repo view "%GH_USER%/%REPO%" >nul 2>nul
if errorlevel 1 (
  echo Repo does not exist. Creating %GH_USER%/%REPO% ...
  gh repo create "%REPO%" --public --source=. --remote=origin --push
  if errorlevel 1 (
    echo Failed to create repo.
    pause
    exit /b 1
  )
) else (
  echo Repo already exists. Ensuring remote and pushing...
  git remote get-url origin >nul 2>nul
  if errorlevel 1 (
    git remote add origin https://github.com/%GH_USER%/%REPO%.git
  ) else (
    git remote set-url origin https://github.com/%GH_USER%/%REPO%.git
  )
  git push -u origin main
)

echo == Done ==
echo https://github.com/%GH_USER%/%REPO%
pause
