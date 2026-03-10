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
    --add-data "src/foreground_tracker.py;." ^
    --add-data "src/settings_window.py;." ^
    --add-data "src/autostart.py;." ^
    --add-data "src/theme.py;." ^
    --add-data "src/widgets.py;." ^
    --add-data "src/break_scheduler.py;." ^
    --add-data "src/break_popup.py;." ^
    --add-data "assets/icon.png;assets" ^
    --add-data "assets/sounds;assets/sounds" ^
    --hidden-import pystray._win32 ^
    src/sticky_alarm.py

echo.
if not exist "1_Export" mkdir "1_Export"
copy /Y dist\StickyAlarm.exe 1_Export\StickyAlarm.exe
echo Done! Output: 1_Export\StickyAlarm.exe
pause
