# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['asc_file_splitter.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['tkinter', 'tkinter.ttk', 'tkinter.filedialog', 'tkinter.messagebox'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib', 'numpy', 'scipy', 'pandas', 'PIL', 'cv2', 'tensorflow',
        'torch', 'sklearn', 'seaborn', 'plotly', 'bokeh', 'altair',
        'jupyter', 'IPython', 'notebook', 'qtconsole', 'spyder',
        'PyQt5', 'PyQt6', 'PySide2', 'PySide6', 'wx',
        'django', 'flask', 'fastapi', 'requests', 'urllib3',
        'pytest', 'unittest', 'nose', 'coverage',
        'sphinx', 'docutils', 'jinja2', 'markupsafe',
        'setuptools', 'pip', 'wheel', 'distutils'
    ],
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
    name='ASC文件分割器',
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
    cofile=None,
    icon=None,
)