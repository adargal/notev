# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Notev
Creates a standalone Windows executable.
"""

import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect all necessary data files
datas = [
    ('notev_frontend/templates', 'notev_frontend/templates'),
    ('notev_frontend/static', 'notev_frontend/static'),
    ('notev_backend', 'notev_backend'),
    ('config.py', '.'),
]

# Hidden imports that PyInstaller might miss
hiddenimports = [
    'flask',
    'flask_cors',
    'anthropic',
    'voyageai',
    'httpx',
    'numpy',
    'docx',
    'pptx',
    'pypdf',
    'werkzeug',
    'jinja2',
    'markupsafe',
    'dotenv',
    'json',
    'pathlib',
    # Add submodules
    'anthropic._client',
    'anthropic.resources',
    'anthropic.types',
    'voyageai.client',
    'httpx._transports',
    'httpx._transports.default',
    'engineio.async_drivers.threading',
]

# Collect submodules for complex packages
hiddenimports += collect_submodules('anthropic')
hiddenimports += collect_submodules('voyageai')
hiddenimports += collect_submodules('httpx')
hiddenimports += collect_submodules('flask')
hiddenimports += collect_submodules('docx')
hiddenimports += collect_submodules('pptx')
hiddenimports += collect_submodules('pypdf')

a = Analysis(
    ['notev_launcher.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'pytest',
        'pytest_cov',
        'gunicorn',
        'tkinter',
        'matplotlib',
        'scipy',
        'pandas',
    ],
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
    name='Notev',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Show console for debugging; set to False for production
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path here if you have one: icon='notev.ico'
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Notev',
)
