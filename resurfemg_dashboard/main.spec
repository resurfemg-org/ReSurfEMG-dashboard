# -*- mode: python ; coding: utf-8 -*-
import sys
import os

block_cipher = None

try:
    project_dir = os.path.abspath(os.path.dirname(__file__))
except NameError:
    project_dir = os.path.abspath(os.path.dirname(sys.argv[0]))

import mne
import trace_updater

mne_path = mne.__path__[0]
trace_updater_path = trace_updater.__path__[0]

a = Analysis(
    ['main.py'],
    pathex=[project_dir],
    binaries=[],
    datas=[
        (os.path.join(project_dir, 'pages'), 'pages'),
        (os.path.join(project_dir, '..', 'resources'), 'resources'),
        (mne_path, 'mne'),
        (trace_updater_path, 'trace_updater'),
    ],
    hiddenimports=[],
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
    name='resurfemg_dashboard',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='main',
)
