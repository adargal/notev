@echo off
REM Notev Build Script for Windows
REM Creates a standalone EXE using PyInstaller
REM
REM IMPORTANT: Run this script from a local Windows folder, NOT from WSL path!
REM Copy the project to C:\Users\YourName\notev first.

echo ============================================================
echo   Notev Build Script
echo ============================================================
echo.

REM Check if running from UNC path (WSL)
echo %CD% | findstr /i "wsl$" >nul
if not errorlevel 1 (
    echo ============================================================
    echo   ERROR: Cannot build from WSL path
    echo ============================================================
    echo.
    echo You are running from: %CD%
    echo.
    echo Please copy the project to a local Windows folder first:
    echo.
    echo   1. Open File Explorer
    echo   2. Copy this folder to C:\Users\YourName\notev
    echo   3. Open Command Prompt in that folder
    echo   4. Run build_exe.bat again
    echo.
    echo Or use this command in PowerShell:
    echo   Copy-Item -Path "\\wsl$\Ubuntu-24.04\home\adar\dev\notev" -Destination "C:\notev" -Recurse
    echo ============================================================
    pause
    exit /b 1
)

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    py --version >nul 2>&1
    if errorlevel 1 (
        echo ============================================================
        echo   ERROR: Python is not installed or not in PATH
        echo ============================================================
        echo.
        echo To build the EXE, you need Python installed:
        echo.
        echo 1. Download Python from: https://www.python.org/downloads/
        echo 2. Run the installer
        echo 3. IMPORTANT: Check "Add Python to PATH" during installation
        echo 4. Close and reopen Command Prompt
        echo 5. Run this script again
        echo.
        echo After the EXE is built, you won't need Python to run it.
        echo ============================================================
        pause
        exit /b 1
    ) else (
        set PYTHON=py
        set PIP=py -m pip
    )
) else (
    set PYTHON=python
    set PIP=python -m pip
)

echo Using: %PYTHON%

REM Check if PyInstaller is installed
%PIP% show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo.
    echo PyInstaller not found. Installing...
    %PIP% install pyinstaller
)

REM Install dependencies
echo.
echo Installing dependencies...
%PIP% install -r requirements.txt

REM Clean previous builds
echo.
echo Cleaning previous builds...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist

REM Build the EXE
echo.
echo Building Notev EXE...
%PYTHON% -m PyInstaller notev.spec --clean

REM Check if build succeeded
if exist "dist\Notev\Notev.exe" (
    echo.
    echo ============================================================
    echo   BUILD SUCCESSFUL!
    echo ============================================================
    echo.
    echo Your distributable is in: dist\Notev\
    echo.
    echo To run: dist\Notev\Notev.exe
    echo.
    echo To distribute, copy the entire 'dist\Notev' folder.
) else (
    echo.
    echo ============================================================
    echo   BUILD FAILED
    echo ============================================================
    echo Please check the error messages above.
)

pause
