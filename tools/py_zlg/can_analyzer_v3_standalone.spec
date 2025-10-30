# -*- mode: python ; coding: utf-8 -*-

# CAN信号分析器 PyInstaller 配置文件 - 独立exe版本 v3.0
# 生成单独的exe文件，包含所有最新功能

a = Analysis(
    ['multi_signal_chart_viewer.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('help_texts', 'help_texts'),  # 包含帮助文本目录
        ('help_manager.py', '.'),     # 包含帮助管理器
    ],
    hiddenimports=[
        # 核心GUI模块
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        
        # 图表绘制模块
        'matplotlib',
        'matplotlib.pyplot',
        'matplotlib.backends.backend_tkagg',
        'matplotlib.figure',
        'matplotlib.ticker',
        
        # 数值计算模块
        'numpy',
        'statistics',
        'math',
        
        # 系统和文件处理
        'os',
        'sys',
        'pathlib',
        'io',
        'struct',
        'time',
        'datetime',
        're',
        'json',
        'pickle',   # 添加pickle模块
        'secrets',  # 添加secrets模块
        'html',     # 添加html模块（matplotlib需要）
        
        # 文件编码检测
        'chardet',
        
        # 数据结构
        'collections',
        'functools',
        'itertools',
        
        # 其他可能需要的模块
        'threading',
        'queue',
        'gzip',
        'zipfile',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 排除不需要的模块以减小体积
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
        'doctest',
        'pdb',
        'pydoc',
        'sqlite3',
        'ssl',
        'ftplib',
        'smtplib',
        'poplib',
        'imaplib',
        'email',
        'csv',
        'audioop',
        'wave',
        'chunk',
        'sunau',
        'aifc',
        'multiprocessing',
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
    name='CAN信号分析器_v3.0_独立版',
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