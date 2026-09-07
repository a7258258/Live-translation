# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec：打成 dist/Live-translation/Live-translation.exe

from PyInstaller.utils.hooks import collect_all

datas = []
binaries = []
hiddenimports = ["soundcard", "numpy", "faster_whisper", "ctranslate2", "av"]

for pkg in (
    "faster_whisper",
    "ctranslate2",
    "av",
    "soundcard",
    "tokenizers",
    "huggingface_hub",
    "onnxruntime",
):
    try:
        pkg_datas, pkg_binaries, pkg_hidden = collect_all(pkg)
        datas += pkg_datas
        binaries += pkg_binaries
        hiddenimports += pkg_hidden
    except Exception:
        pass

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    name="Live-translation",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="Live-translation",
)
