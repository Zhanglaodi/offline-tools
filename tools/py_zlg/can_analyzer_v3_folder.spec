# -*- mode: python ; coding: utf-8 -*-

# CAN信号分析器 PyInstaller 配置文件 - 文件夹版本 v3.1
# 生成文件夹版本，包含DBC数据库功能和所有最新功能

a = Analysis(
    ['multi_signal_chart_viewer.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('help_texts', 'help_texts'),        # 包含帮助文本目录
        ('help_manager.py', '.'),           # 包含帮助管理器
        ('simple_asc_reader.py', '.'),      # ASC文件解析器
        ('dbc_parser.py', '.'),             # DBC文件解析器（新增）
        ('dbc_plugin.py', '.'),             # DBC插件（新增）
        ('README.md', '.'),                 # 项目说明文档
        ('requirements.txt', '.'),          # 依赖清单
        # 示例文件（如果存在）
        # ('example_vehicle.dbc', '.'),     # 示例DBC文件
        # ('test_vehicle_data.asc', '.'),   # 示例ASC测试数据
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
        
        # DBC相关模块（新增）
        'dataclasses',          # DBC数据模型
        'typing',               # 类型注解支持
        'enum',                 # 枚举类型
        'abc',                  # 抽象基类
        
        # 项目模块（显式导入）
        'simple_asc_reader',    # ASC文件解析器
        'dbc_parser',           # DBC文件解析器
        'dbc_plugin',           # DBC插件
        'help_manager',         # 帮助管理器
        
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
    [],
    exclude_binaries=True,  # 关键：生成文件夹版本
    name='CAN信号分析器_v3.1_DBC版',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # 不显示控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='CAN信号分析器_v3.1_DBC文件夹版',
)