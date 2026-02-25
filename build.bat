@echo off
echo Installing dependencies...
pip install -r requirements.txt pyinstaller

echo.
echo Building StickyAlarm.exe...
pyinstaller --onefile --windowed --name="StickyAlarm" --icon=icon.ico ^
    --add-data "config.py;." ^
    --add-data "scheduler.py;." ^
    --add-data "popup.py;." ^
    --add-data "chrome_monitor.py;." ^
    --add-data "settings_window.py;." ^
    --add-data "autostart.py;." ^
    --hidden-import pystray._win32 ^
    sticky_alarm.py

echo.
echo Done! Output: dist\StickyAlarm.exe
pause
