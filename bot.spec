# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['celestialsentry.py'],
    pathex=[],
    binaries=[],
    # We are letting the Python script create its own data files at runtime.
    datas=[],
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
    console=False,
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