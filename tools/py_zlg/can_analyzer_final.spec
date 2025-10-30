# -*- mode: python ; coding: utf-8 -*-

# CAN信号分析器 PyInstaller 配置文件 - 最终版本
# 采用最保守策略，不排除任何模块，让PyInstaller自动处理依赖

a = Analysis(
    ['multi_signal_chart_viewer.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('help_texts', 'help_texts'),  # 包含帮助文本目录
    ],
    hiddenimports=[
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'matplotlib.backends.backend_tkagg',
        'numpy',
        'statistics',
        'collections',
        'pathlib',
        'zipfile',
        'gzip',
        'io',
        'os',
        'sys',
        'chardet',
        'urllib',
        'urllib.parse',
        'urllib.request',
        'urllib.error',
        're',
        'struct',
        'math',
        'time',
        'datetime',
        'random',
        'functools',
        'itertools',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 只排除明确已知不需要的开发工具
        'pytest',
        'jupyter',
        'notebook',
        'IPython',
        'setuptools',
        'distutils',
        'test',
        'tests',
        'testing',
        'unittest',
    ],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='CAN信号分析器_完整版',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 不显示控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)