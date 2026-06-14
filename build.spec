# PyInstaller spec for Simple AutoClicker
# Build: pyinstaller build.spec

from pathlib import Path

from PyInstaller.utils.hooks import collect_all

block_cipher = None
project_dir = Path(SPECPATH)
files_dir = project_dir / "simple_autoclicker" / "files"
icon_file = files_dir / "autoclicker_pro_v5.ico"
asset_files = [
    (str(files_dir / "autoclicker_v5_256.png"), "simple_autoclicker/files"),
    (str(files_dir / "autoclicker_pro_v5.ico"), "simple_autoclicker/files"),
]

ctk_datas, ctk_binaries, ctk_hiddenimports = collect_all("customtkinter")

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=ctk_binaries,
    datas=ctk_datas + asset_files,
    hiddenimports=ctk_hiddenimports + [
        "pynput.keyboard._win32",
        "pynput.mouse._win32",
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="Simple AutoClicker",
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
    icon=str(icon_file) if icon_file.is_file() else None,
)
