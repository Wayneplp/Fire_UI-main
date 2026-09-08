# -*- mode: python ; coding: utf-8 -*-
# 单文件 exe 调试版（保留控制台）

from pathlib import Path
import sys

conda_bin = Path(sys.prefix) / 'Library' / 'bin'

a = Analysis(
    ['can_init.py'],
    pathex=[],
    binaries=[
        ('.\\PCANBasic.dll', '.'),
        (str(conda_bin / 'ffi.dll'), '.'),
        (str(conda_bin / 'sqlite3.dll'), '.'),
    ],
    datas=[('base/www', 'base/www')],
    hiddenimports=[
        'can',
        'can.interfaces.pcan',
        'can.interfaces.pcan.pcan',
        'can.interfaces.pcan.basic',
        'webview',
        'webview.platforms.winforms',
        'webview.platforms.edgechromium',
        'clr',
        'bottle',
        'proxy_tools',
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
    name='百安消防主站_Debug',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
