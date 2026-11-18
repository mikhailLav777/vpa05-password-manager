@echo off
setlocal
cd /d "%~dp0"

py -3.12 -m venv .build-venv
if errorlevel 1 goto failed

".build-venv\Scripts\python.exe" -m pip install pyinstaller
if errorlevel 1 goto failed

".build-venv\Scripts\python.exe" -m PyInstaller --noconfirm --onefile --windowed --name PasswordGenerator generator_gui.py
if errorlevel 1 goto failed

if not exist "dist\PasswordGenerator.exe" goto failed
echo.
echo The generator is ready: dist\PasswordGenerator.exe
pause
exit /b 0

:failed
echo.
echo Build did not finish. See the error above.
pause
exit /b 1
