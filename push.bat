@echo off
cls
cd /d "%~dp0"

set "msg=%*"

if "%msg%"=="" set "msg=Commit"

git add .
git commit -m "%msg%"
git push origin main