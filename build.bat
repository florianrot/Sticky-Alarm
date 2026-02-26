@echo off
cd /d "%~dp0"

echo Installing dependencies...
pip install -r requirements.txt pyinstaller

echo.
echo Building StickyAlarm.exe...
pyinstaller --onefile --windowed --name="StickyAlarm" --icon=assets/icon.ico ^
    --add-data "src/config.py;." ^
    --add-data "src/scheduler.py;." ^
    --add-data "src/popup.py;." ^
    --add-data "src/chrome_monitor.py;." ^
    --add-data "src/settings_window.py;." ^
    --add-data "src/autostart.py;." ^
    --add-data "src/theme.py;." ^
    --add-data "src/widgets.py;." ^
    --hidden-import pystray._win32 ^
    src/sticky_alarm.py

echo.
echo Done! Output: dist\StickyAlarm.exe
pause
