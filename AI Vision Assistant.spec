# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_data_files

mediapipe_datas = collect_data_files('mediapipe')

a = Analysis(
    ['frontend/app.py'],
    pathex=['backend', 'frontend'],
    binaries=[],
    datas=[
        ('backend', 'backend'),
        ('frontend/assets', 'frontend/assets'),
        *mediapipe_datas,
    ],
    hiddenimports=[
        'mediapipe', 'cv2', 'pyautogui', 'pycaw', 'comtypes',
        'screen_brightness_control', 'pyttsx3', 'customtkinter',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AI Vision Assistant',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AI Vision Assistant',
)
