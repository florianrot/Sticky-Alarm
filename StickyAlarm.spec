# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['src\\sticky_alarm.py'],
    pathex=[],
    binaries=[],
    datas=[('src/config.py', '.'), ('src/scheduler.py', '.'), ('src/popup.py', '.'), ('src/chrome_monitor.py', '.'), ('src/foreground_tracker.py', '.'), ('src/settings_window.py', '.'), ('src/autostart.py', '.'), ('src/theme.py', '.'), ('src/widgets.py', '.'), ('src/break_scheduler.py', '.'), ('src/break_popup.py', '.'), ('assets/icon.png', 'assets'), ('assets/sounds', 'assets/sounds')],
    hiddenimports=['pystray._win32'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='StickyAlarm',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets\\icon.ico'],
)
