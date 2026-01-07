# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Notev
Creates a standalone Windows executable with local embeddings support.
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

# Collect data files for sentence-transformers and transformers
try:
    datas += collect_data_files('sentence_transformers')
except Exception:
    pass

try:
    datas += collect_data_files('transformers')
except Exception:
    pass

# Hidden imports that PyInstaller might miss
hiddenimports = [
    # Web framework
    'flask',
    'flask_cors',
    'werkzeug',
    'jinja2',
    'markupsafe',
    'click',
    'itsdangerous',
    'blinker',

    # AI/API
    'anthropic',
    'httpx',

    # Document processing
    'docx',
    'pptx',
    'pypdf',

    # Data processing
    'numpy',
    'dotenv',
    'json',
    'pathlib',

    # Local embeddings
    'sentence_transformers',
    'transformers',
    'torch',
    'tokenizers',
    'huggingface_hub',
    'safetensors',
    'tqdm',
    'regex',
    'requests',
    'filelock',

    # BM25 search
    'rank_bm25',

    # Submodules
    'anthropic._client',
    'anthropic.resources',
    'anthropic.types',
    'httpx._transports',
    'httpx._transports.default',
    'engineio.async_drivers.threading',
]

# Collect submodules for complex packages
hiddenimports += collect_submodules('anthropic')
hiddenimports += collect_submodules('httpx')
hiddenimports += collect_submodules('flask')
hiddenimports += collect_submodules('docx')
hiddenimports += collect_submodules('pptx')
hiddenimports += collect_submodules('pypdf')

# Collect sentence-transformers and transformers submodules
try:
    hiddenimports += collect_submodules('sentence_transformers')
except Exception:
    pass

try:
    hiddenimports += collect_submodules('transformers')
except Exception:
    pass

try:
    hiddenimports += collect_submodules('tokenizers')
except Exception:
    pass

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
        # Testing
        'pytest',
        'pytest_cov',

        # Server (not needed for EXE)
        'gunicorn',

        # GUI (not used)
        'tkinter',

        # Heavy scientific packages (not needed)
        'matplotlib',
        'scipy',
        'pandas',

        # CUDA/GPU (force CPU only for smaller size)
        'torch.cuda',
        'torch.distributed',
        'torch.testing',
        'torch.utils.tensorboard',
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
