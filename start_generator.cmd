@echo off
setlocal
cd /d "%~dp0"
py -3.12 "%~dp0generator_gui.py"
if errorlevel 1 (
    echo Could not start the generator. Check that Python 3.12 and Tkinter are installed.
    pause
)
