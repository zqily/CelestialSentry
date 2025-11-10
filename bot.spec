# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['celestialsentry.py'],
    pathex=[],
    binaries=[],
    # --- CHANGE: The 'datas' list is now empty ---
    # We are letting the Python script create its own data files at runtime.
    datas=[],
    # --- Hidden imports are still required ---
    hiddenimports=[
        'discord',
        'discord.ext.commands',
        'discord.ext.tasks',
        'aiohttp',
        'async_timeout',
        'websockets',
        'charset_normalizer',
        'idna',
        'multidict',
        'yarl'
    ],
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
    name='CelestialSentry',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    # Keep console=True for now to see logs and errors easily.
    # Change to False for the final version to run in the background.
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # This line sets the icon for the .exe file.
    # PyInstaller will look for 'icon.ico' in the project root.
    # Remove this line if you don't want a custom icon.
    icon='icon.ico',
)