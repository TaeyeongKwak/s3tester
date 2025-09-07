@echo off
REM S3Tester Binary Build Script for Windows

echo 🔧 S3Tester Binary Build Script
echo ================================

REM Check if virtual environment is active
if not defined VIRTUAL_ENV (
    echo ❌ Virtual environment not detected. Please activate your virtual environment first:
    echo    venv\Scripts\activate
    exit /b 1
)

echo ✅ Virtual environment detected: %VIRTUAL_ENV%

REM Install build dependencies
echo 📦 Installing build dependencies...
pip install -e ".[build]"

REM Clean previous builds
echo 🧹 Cleaning previous build artifacts...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
for /d /r %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
del /s /q *.pyc >nul 2>&1

REM Run PyInstaller
echo 🔨 Building binary executable...
pyinstaller s3tester.spec

REM Check if build was successful
if exist "dist\s3tester.exe" (
    echo ✅ Binary executable built successfully!
    echo 📍 Location: dist\
    dir dist\
    
    echo.
    echo 🚀 Test the executable:
    echo    dist\s3tester.exe --version
    echo    dist\s3tester.exe --help
) else (
    echo ❌ Build failed! Check the output above for errors.
    exit /b 1
)

echo.
echo ✨ Build completed successfully!