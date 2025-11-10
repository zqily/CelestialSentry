# -*- mode: python ; coding: utf-8 -*-

# This is a PyInstaller spec file for 'celestialsentry.py'.
# Save this file as 'bot.spec' in the same directory as your script and 'icon.ico'.
#
# To build the executable, open a terminal in this directory and run:
#   pyinstaller bot.spec
#
# This will create a 'dist' folder containing 'celestialsentry.exe'.
# For a single-file executable (recommended for distribution), run:
#   pyinstaller bot.spec --onefile
#
# --- DEPLOYMENT INSTRUCTIONS ---
# 1. Place the generated 'celestialsentry.exe' from the 'dist' folder into a new, clean folder.
# 2. Create a file named '.env' in that same folder.
# 3. Add your Discord token to the .env file like this:
#    DISCORD_TOKEN="your_actual_bot_token_here"
# 4. Run celestialsentry.exe. The bot will start and create its log and data files (bot.log, config.json, etc.).

block_cipher = None

a = Analysis(
    ['celestialsentry.py'],
    pathex=[],
    binaries=[],
    datas=[],  # We do not bundle data files like '.env' or 'config.json'.
               # The script is specifically designed to find or create these files
               # in the same directory as the executable at runtime.
               # This approach correctly avoids packaging sensitive information
               # (like the Discord token) into the final executable.
    hiddenimports=[
        'dotenv',  # Ensure the dotenv library is explicitly included.
        'aiohttp', # discord.py depends on this; including it helps prevent runtime errors.
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='celestialsentry',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,         # True: A command window will be shown. This is highly
                          # recommended to see startup logs and potential errors.
                          # False: The app runs in the background with no window.
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',      # Specifies the icon for the .exe file.
                          # Make sure 'icon.ico' is in the same directory as this spec file.
)

# The COLLECT block is used for one-folder builds.
# When using the --onefile flag, PyInstaller intelligently bundles
# everything specified here into the single .exe file instead.
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='celestialsentry',
)