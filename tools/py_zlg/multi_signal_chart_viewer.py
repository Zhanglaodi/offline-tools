#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CAN多信号曲线图查看器
支持同时显示多个CAN ID和多个信号的曲线
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from pathlib import Path
from collections import defaultdict
import random
import statistics
import numpy as np

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from simple_asc_reader import SimpleASCReader
from help_manager import HelpTextManager
from dbc_plugin import DBCPlugin

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

class MultiSignalChartViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("CAN多信号曲线图查看器")
        
        # 设置窗口全屏
        self.setup_window()
        
        # 数据存储
        self.messages = []
        self.signal_configs = []  # 存储多个信号配置
        self.colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan']
        
        # 界面控制变量
        self.crosshair_enabled = tk.BooleanVar(value=True)
        self.measurement_mode = tk.BooleanVar(value=False)
        
        # 测量相关变量
        self.measurement_points = []  # 存储测量点 [(x1, y1), (x2, y2)]
        self.measurement_lines = {}   # 存储测量线
        self.measurement_annotations = {}  # 存储测量标注
        
        # 性能优化缓存
        self.frame_stats_cache = {}  # 缓存帧统计结果
        self.signal_data_cache = {}  # 缓存信号提取结果
        self.last_update_time = 0    # 最后更新时间
        
        # 性能优化缓存
        self.frame_stats_cache = {}  # 缓存帧统计结果
        self.signal_data_cache = {}  # 缓存信号数据
        self.dropped_frames_cache = {}  # 缓存丢帧检测结果
        
        # 帮助文本管理器
        self.help_manager = HelpTextManager()
        
        # DBC插件初始化
        self.dbc_plugin = None
        
        # 创建界面
        self.create_widgets()
        
        # 初始化DBC插件
        self.init_dbc_plugin()
    
    def setup_window(self):
        """设置窗口属性"""
        # 获取屏幕尺寸
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # 方式1: 最大化窗口（推荐）
        try:
            self.root.state('zoomed')  # Windows下最大化
        except tk.TclError:
            # 对于不支持zoomed的系统，使用全屏尺寸
            self.root.geometry(f"{screen_width}x{screen_height}+0+0")
        
        # 设置最小窗口尺寸，防止窗口过小
        self.root.minsize(1000, 700)
        
        # 绑定快捷键
        self.root.bind('<F11>', self.toggle_fullscreen)
        self.root.bind('<Escape>', self.exit_fullscreen)
        
        # 全屏状态标志
        self.is_fullscreen = False
    
    def toggle_fullscreen(self, event=None):
        """切换全屏状态"""
        self.is_fullscreen = not self.is_fullscreen
        if self.is_fullscreen:
            self.root.attributes('-fullscreen', True)
        else:
            self.root.attributes('-fullscreen', False)
    
    def exit_fullscreen(self, event=None):
        """退出全屏"""
        self.is_fullscreen = False
        self.root.attributes('-fullscreen', False)
    
    def create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="打开ASC文件", command=self.load_file, accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit, accelerator="Ctrl+Q")
        
        # 视图菜单
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="视图", menu=view_menu)
        view_menu.add_checkbutton(label="显示网格", variable=self.show_grid_var, command=self.update_chart)
        view_menu.add_checkbutton(label="子图模式", variable=self.subplot_mode_var, command=self.update_chart)
        view_menu.add_checkbutton(label="显示丢帧点", variable=self.show_dropped_frames_var, command=self.update_chart)
        view_menu.add_separator()
        view_menu.add_command(label="切换全屏", command=self.toggle_fullscreen, accelerator="F11")
        view_menu.add_separator()
        view_menu.add_command(label="清除所有信号", command=self.clear_signals)
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="使用指南", command=self.show_user_guide)
        help_menu.add_command(label="快捷键", command=self.show_shortcuts)
        help_menu.add_command(label="功能说明", command=self.show_features)
        help_menu.add_separator()
        help_menu.add_command(label="关于", command=self.show_about)
        
        # 绑定快捷键
        self.root.bind('<Control-o>', lambda e: self.load_file())
        self.root.bind('<Control-q>', lambda e: self.root.quit())
        self.root.bind('<F1>', lambda e: self.show_user_guide())
    
    def create_widgets(self):
        """创建界面组件"""
        # 先定义菜单相关变量
        self.show_grid_var = tk.BooleanVar(value=True)
        self.show_legend_var = tk.BooleanVar(value=True)
        self.subplot_mode_var = tk.BooleanVar(value=False)
        self.show_dropped_frames_var = tk.BooleanVar(value=False)
        
        # 创建菜单
        self.create_menu()
        
        # 主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 左侧控制面板容器（带滚动条）
        control_container = ttk.LabelFrame(main_frame, text="控制面板", padding=5)
        control_container.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # 创建滚动画布 - 增加宽度以适应DBC内容
        self.control_canvas = tk.Canvas(control_container, width=420, highlightthickness=0, bg='white')
        control_scrollbar = ttk.Scrollbar(control_container, orient="vertical", command=self.control_canvas.yview)
        self.control_scrollable_frame = ttk.Frame(self.control_canvas)
        
        # 配置滚动区域
        def configure_scroll_region(event=None):
            self.control_canvas.configure(scrollregion=self.control_canvas.bbox("all"))
        
        self.control_scrollable_frame.bind("<Configure>", configure_scroll_region)
        
        # 创建画布窗口
        canvas_window = self.control_canvas.create_window((0, 0), window=self.control_scrollable_frame, anchor="nw")
        
        # 配置画布窗口宽度自适应
        def configure_canvas_width(event=None):
            canvas_width = self.control_canvas.winfo_width()
            self.control_canvas.itemconfig(canvas_window, width=canvas_width)
        
        self.control_canvas.bind('<Configure>', configure_canvas_width)
        self.control_canvas.configure(yscrollcommand=control_scrollbar.set)
        
        # 打包滚动组件
        self.control_canvas.pack(side="left", fill="both", expand=True)
        control_scrollbar.pack(side="right", fill="y")
        
        # 现在control_frame指向可滚动的框架
        control_frame = self.control_scrollable_frame
        
        # 文件选择
        file_frame = ttk.Frame(control_frame)
        file_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Button(file_frame, text="选择ASC文件", command=self.load_file).pack(fill=tk.X)
        self.file_label = ttk.Label(file_frame, text="未选择文件", foreground="gray")
        self.file_label.pack(fill=tk.X, pady=(5, 0))
        
        # 信号添加区域
        self.add_frame = ttk.LabelFrame(control_frame, text="添加信号", padding=5)
        self.add_frame.pack(fill=tk.X, pady=(0, 10))
        
        # CAN ID选择
        id_frame = ttk.Frame(self.add_frame)
        id_frame.pack(fill=tk.X, pady=2)
        ttk.Label(id_frame, text="CAN ID:", width=8).pack(side=tk.LEFT)
        self.can_id_var = tk.StringVar()
        self.can_id_combo = ttk.Combobox(id_frame, textvariable=self.can_id_var, state="readonly", width=15)
        self.can_id_combo.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 0))
        
        # DBC数据库支持（将在init_dbc_plugin中初始化）
        self.dbc_frame = None
        
        # 信号配置
        ttk.Separator(self.add_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)
        
        # 起始位
        start_frame = ttk.Frame(self.add_frame)
        start_frame.pack(fill=tk.X, pady=2)
        ttk.Label(start_frame, text="起始位:", width=8).pack(side=tk.LEFT)
        self.start_bit_var = tk.StringVar(value="0")
        ttk.Entry(start_frame, textvariable=self.start_bit_var, width=10).pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 0))
        
        # 长度
        length_frame = ttk.Frame(self.add_frame)
        length_frame.pack(fill=tk.X, pady=2)
        ttk.Label(length_frame, text="长度:", width=8).pack(side=tk.LEFT)
        self.length_var = tk.StringVar(value="8")
        ttk.Entry(length_frame, textvariable=self.length_var, width=10).pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 0))
        
        # 系数
        factor_frame = ttk.Frame(self.add_frame)
        factor_frame.pack(fill=tk.X, pady=2)
        ttk.Label(factor_frame, text="系数:", width=8).pack(side=tk.LEFT)
        self.factor_var = tk.StringVar(value="1.0")
        ttk.Entry(factor_frame, textvariable=self.factor_var, width=10).pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 0))
        
        # 偏移
        offset_frame = ttk.Frame(self.add_frame)
        offset_frame.pack(fill=tk.X, pady=2)
        ttk.Label(offset_frame, text="偏移:", width=8).pack(side=tk.LEFT)
        self.offset_var = tk.StringVar(value="0.0")
        ttk.Entry(offset_frame, textvariable=self.offset_var, width=10).pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 0))
        
        # 有符号
        self.signed_var = tk.BooleanVar()
        ttk.Checkbutton(self.add_frame, text="有符号数", variable=self.signed_var).pack(anchor=tk.W, pady=2)
        
        # 字节序选择
        endian_frame = ttk.Frame(self.add_frame)
        endian_frame.pack(fill=tk.X, pady=2)
        ttk.Label(endian_frame, text="字节序:", width=8).pack(side=tk.LEFT)
        self.endian_var = tk.StringVar(value="little")
        self.endian_combo = ttk.Combobox(endian_frame, textvariable=self.endian_var, 
                                   values=["big", "little"], state="readonly", width=10)
        self.endian_combo.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 0))
        
        # 字节序说明
        endian_info = ttk.Label(self.add_frame, text="big=大端(Motorola), little=小端(Intel)", 
                               font=("Arial", 8), foreground="gray")
        endian_info.pack(anchor=tk.W, pady=(0, 2))
        
        # 信号名称
        name_frame = ttk.Frame(self.add_frame)
        name_frame.pack(fill=tk.X, pady=2)
        ttk.Label(name_frame, text="名称:", width=8).pack(side=tk.LEFT)
        self.signal_name_var = tk.StringVar(value="信号1")
        ttk.Entry(name_frame, textvariable=self.signal_name_var, width=10).pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 0))
        
        # 添加按钮
        button_frame = ttk.Frame(self.add_frame)
        button_frame.pack(fill=tk.X, pady=(5, 0))
        self.add_signal_btn = ttk.Button(button_frame, text="添加信号", command=self.add_signal)
        self.add_signal_btn.pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="清除全部", command=self.clear_signals).pack(side=tk.RIGHT)
        
        # 信号列表
        list_frame = ttk.LabelFrame(control_frame, text="信号列表", padding=5)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 创建列表框和滚动条
        list_container = ttk.Frame(list_frame)
        list_container.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.signal_listbox = tk.Listbox(list_container, yscrollcommand=scrollbar.set, height=8)
        self.signal_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.signal_listbox.yview)
        
        # 列表操作按钮
        list_btn_frame = ttk.Frame(list_frame)
        list_btn_frame.pack(fill=tk.X, pady=(5, 0))
        ttk.Button(list_btn_frame, text="删除选中", command=self.remove_signal).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(list_btn_frame, text="统计详情", command=self.show_signal_stats).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(list_btn_frame, text="更新图表", command=self.update_chart).pack(side=tk.RIGHT)
        
        # 显示选项
        display_frame = ttk.LabelFrame(control_frame, text="显示选项", padding=5)
        display_frame.pack(fill=tk.X)
        
        self.show_legend_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(display_frame, text="显示图例", variable=self.show_legend_var,
                       command=self.update_chart).pack(anchor=tk.W)
        
        self.show_grid_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(display_frame, text="显示网格", variable=self.show_grid_var,
                       command=self.update_chart).pack(anchor=tk.W)
        
        ttk.Checkbutton(display_frame, text="显示十字线", variable=self.crosshair_enabled,
                       command=self.toggle_crosshair).pack(anchor=tk.W)
        
        ttk.Checkbutton(display_frame, text="测量模式", variable=self.measurement_mode,
                       command=self.toggle_measurement_mode).pack(anchor=tk.W)
        
        ttk.Checkbutton(display_frame, text="子图模式", variable=self.subplot_mode_var,
                       command=self.update_chart).pack(anchor=tk.W)
        
        ttk.Checkbutton(display_frame, text="显示丢帧点", variable=self.show_dropped_frames_var,
                       command=self.update_chart).pack(anchor=tk.W)
        
        # 时间范围控制
        time_frame = ttk.LabelFrame(control_frame, text="时间范围", padding=5)
        time_frame.pack(fill=tk.X, pady=(5, 0))
        
        time_input_frame = ttk.Frame(time_frame)
        time_input_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(time_input_frame, text="开始:", width=6).pack(side=tk.LEFT)
        self.time_start_var = tk.StringVar(value="")
        self.time_start_entry = ttk.Entry(time_input_frame, textvariable=self.time_start_var, width=12)
        self.time_start_entry.pack(side=tk.LEFT, padx=(0, 5), fill=tk.X, expand=True)
        
        ttk.Label(time_input_frame, text="结束:", width=6).pack(side=tk.LEFT)
        self.time_end_var = tk.StringVar(value="")
        self.time_end_entry = ttk.Entry(time_input_frame, textvariable=self.time_end_var, width=12)
        self.time_end_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        time_btn_frame = ttk.Frame(time_frame)
        time_btn_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(time_btn_frame, text="应用范围", command=self.apply_time_range).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(time_btn_frame, text="重置范围", command=self.reset_time_range).pack(side=tk.LEFT)
        
        # 右侧图表区域
        chart_frame = ttk.Frame(main_frame)
        chart_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 创建图表
        self.figure = Figure(figsize=(10, 8), dpi=100)
        # 设置figure的一些优化选项
        self.figure.patch.set_facecolor('white')
        self.canvas = FigureCanvasTkAgg(self.figure, chart_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 添加工具栏（支持缩放、平移等）
        self.toolbar = NavigationToolbar2Tk(self.canvas, chart_frame)
        self.toolbar.update()
        
        # 存储时间范围和子图同步
        self.current_time_range = None
        self.axes_list = []  # 存储所有子图
        self.subplot_mode_active = False
        
        # 连接事件处理器
        self.canvas.mpl_connect('button_release_event', self.on_mouse_release)
        self.canvas.mpl_connect('scroll_event', self.on_mouse_scroll)
        self.canvas.mpl_connect('button_press_event', self.on_mouse_press)
        self.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)
        
        # 滚轮缩放设置
        self.zoom_factor = 1.1  # 缩放倍数
        
        # 拖拽状态
        self.dragging = False
        self.drag_start_pos = None
        self.drag_axis = None
        self.last_drag_time = 0  # 用于控制拖拽重绘频率
        self.drag_update_pending = False  # 防止重复的更新请求
        
        # 垂直线和数据显示
        self.vlines = {}  # 存储每个子图的垂直线
        self.data_annotations = {}  # 存储数据标注
        
        # 状态栏
        self.status_label = ttk.Label(self.root, text="请选择ASC文件并添加信号", relief=tk.SUNKEN)
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 绑定控制面板的鼠标滚轮事件
        self.bind_mousewheel_to_control_panel()
    
    def bind_mousewheel_to_control_panel(self):
        """绑定控制面板的鼠标滚轮事件"""
        def _on_mousewheel(event):
            # 检查鼠标是否在控制面板区域内
            widget = event.widget
            while widget:
                if widget == self.control_canvas:
                    self.control_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
                    break
                widget = widget.master
        
        def _bind_to_mousewheel(widget):
            widget.bind("<MouseWheel>", _on_mousewheel)
            for child in widget.winfo_children():
                _bind_to_mousewheel(child)
        
        # 绑定控制面板及其所有子组件
        _bind_to_mousewheel(self.control_scrollable_frame)
        # 同时绑定画布本身
        self.control_canvas.bind("<MouseWheel>", _on_mousewheel)
    
    def calculate_frame_stats(self, can_id, use_cache=True):
        """计算帧统计信息：丢帧和周期 - 优化版本"""
        # 性能优化：使用缓存
        if use_cache and can_id in self.frame_stats_cache:
            return self.frame_stats_cache[can_id]
        
        try:
            # 优化：使用列表推导式，一次性过滤和提取
            message_data = [(msg['timestamp']) for msg in self.messages if msg['can_id'] == can_id]
            if len(message_data) < 3:
                return None
            
            # 优化：使用numpy排序（如果可用），否则使用内置sort
            timestamps = sorted(message_data)
            
            # 优化：向量化计算间隔
            intervals = [timestamps[i] - timestamps[i-1] for i in range(1, len(timestamps))]
            
            if not intervals:
                return None
            
            # 优化：使用更快的统计方法
            intervals_array = np.array(intervals) if 'np' in globals() else intervals
            
            if isinstance(intervals_array, np.ndarray):
                estimated_period = float(np.median(intervals_array))
                avg_period = float(np.mean(intervals_array))
            else:
                estimated_period = statistics.median(intervals)
                avg_period = statistics.mean(intervals)
            
            # 众数计算优化：只在必要时执行
            if abs(estimated_period - avg_period) > estimated_period * 0.5:
                # 优化的众数计算
                bin_size = 0.001
                interval_counts = {}
                for interval in intervals:
                    bin_key = round(interval / bin_size) * bin_size
                    interval_counts[bin_key] = interval_counts.get(bin_key, 0) + 1
                
                if interval_counts:
                    estimated_period = max(interval_counts, key=interval_counts.get)
            
            # 优化：预计算常用值
            total_time = timestamps[-1] - timestamps[0]
            expected_frames = int(total_time / estimated_period) + 1
            actual_frames = len(message_data)
            dropped_frames = max(0, expected_frames - actual_frames)
            drop_rate = (dropped_frames / expected_frames * 100) if expected_frames > 0 else 0
            
            result = {
                'period_ms': estimated_period * 1000,
                'dropped_frames': dropped_frames,
                'drop_rate': drop_rate,
                'total_frames': actual_frames,
                'expected_frames': expected_frames,
                'time_span': total_time
            }
            
            # 缓存结果
            if use_cache:
                self.frame_stats_cache[can_id] = result
            
            return result
            
        except Exception as e:
            return None
    
    def detect_dropped_frame_positions(self, can_id, estimated_period, use_cache=True):
        """检测丢帧位置 - 高性能优化版本"""
        # 性能优化：缓存key
        cache_key = f"{can_id}_{estimated_period:.6f}"
        if use_cache and cache_key in self.dropped_frames_cache:
            return self.dropped_frames_cache[cache_key]
        
        try:
            # 优化：一次性获取并排序时间戳
            timestamps = sorted([msg['timestamp'] for msg in self.messages if msg['can_id'] == can_id])
            
            if len(timestamps) < 2:
                return []
            
            dropped_positions = []
            tolerance = estimated_period * 0.3
            min_gap = estimated_period + tolerance
            
            # 优化：向量化操作检测间隔
            for i in range(1, len(timestamps)):
                interval = timestamps[i] - timestamps[i-1]
                
                if interval > min_gap:
                    # 优化：更精确的丢帧数计算
                    dropped_count = int((interval / estimated_period) - 0.5)
                    
                    if dropped_count > 0:
                        # 批量计算丢失位置
                        start_time = timestamps[i-1]
                        for j in range(1, dropped_count + 1):
                            dropped_time = start_time + (j * estimated_period)
                            if start_time < dropped_time < timestamps[i]:
                                dropped_positions.append(dropped_time)
            
            # 缓存结果
            if use_cache:
                self.dropped_frames_cache[cache_key] = dropped_positions
            
            return dropped_positions
            
        except Exception as e:
            return []
    
    def interpolate_signal_at_dropped_frames(self, timestamps, values, dropped_times):
        """在丢帧位置插值估算信号值"""
        interpolated_values = []
        
        for drop_time in dropped_times:
            # 找到最近的两个数据点进行线性插值
            before_idx = -1
            after_idx = -1
            
            for i, ts in enumerate(timestamps):
                if ts <= drop_time:
                    before_idx = i
                if ts > drop_time and after_idx == -1:
                    after_idx = i
                    break
            
            # 执行线性插值
            if before_idx >= 0 and after_idx >= 0:
                t1, v1 = timestamps[before_idx], values[before_idx]
                t2, v2 = timestamps[after_idx], values[after_idx]
                
                # 线性插值公式
                ratio = (drop_time - t1) / (t2 - t1) if t2 != t1 else 0
                interpolated_value = v1 + ratio * (v2 - v1)
                interpolated_values.append(interpolated_value)
            elif before_idx >= 0:
                # 只有前面的点，使用最近值
                interpolated_values.append(values[before_idx])
            elif after_idx >= 0:
                # 只有后面的点，使用最近值
                interpolated_values.append(values[after_idx])
            else:
                # 无法插值，使用0
                interpolated_values.append(0)
        
        return interpolated_values
    
    def show_user_guide(self):
        """显示用户指南"""
        guide_window = tk.Toplevel(self.root)
        guide_window.title("CAN信号分析器 - 使用指南")
        guide_window.geometry("800x600")
        guide_window.resizable(True, True)
        
        # 创建滚动文本框
        text_frame = ttk.Frame(guide_window)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        text_widget = tk.Text(text_frame, wrap=tk.WORD, yscrollcommand=scrollbar.set, 
                             font=("Arial", 10), padx=10, pady=10)
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=text_widget.yview)
        
        # 使用帮助管理器加载文本
        guide_text = self.help_manager.get_user_guide()
        text_widget.insert(tk.END, guide_text)
        text_widget.config(state=tk.DISABLED)
        
        # 关闭按钮
        ttk.Button(guide_window, text="关闭", command=guide_window.destroy).pack(pady=10)
    
    def show_shortcuts(self):
        """显示快捷键"""
        shortcuts_window = tk.Toplevel(self.root)
        shortcuts_window.title("快捷键说明")
        shortcuts_window.geometry("500x400")
        shortcuts_window.resizable(False, False)
        
        text_widget = tk.Text(shortcuts_window, wrap=tk.WORD, padx=20, pady=20, font=("Consolas", 11))
        text_widget.pack(fill=tk.BOTH, expand=True)
        
        # 使用帮助管理器加载文本
        shortcuts_text = self.help_manager.get_shortcuts()
        text_widget.insert(tk.END, shortcuts_text)
        text_widget.config(state=tk.DISABLED)
        
        ttk.Button(shortcuts_window, text="关闭", command=shortcuts_window.destroy).pack(pady=10)
    
    def show_features(self):
        """显示功能说明"""
        features_window = tk.Toplevel(self.root)
        features_window.title("功能特性说明")
        features_window.geometry("700x500")
        features_window.resizable(True, True)
        
        # 创建标签页
        notebook = ttk.Notebook(features_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 基础功能标签页
        basic_frame = ttk.Frame(notebook)
        notebook.add(basic_frame, text="基础功能")
        
        basic_text = tk.Text(basic_frame, wrap=tk.WORD, padx=10, pady=10)
        basic_text.pack(fill=tk.BOTH, expand=True)
        basic_content = self.help_manager.get_features_basic()
        basic_text.insert(tk.END, basic_content)
        basic_text.config(state=tk.DISABLED)
        
        # 高级功能标签页
        advanced_frame = ttk.Frame(notebook)
        notebook.add(advanced_frame, text="高级功能")
        
        advanced_text = tk.Text(advanced_frame, wrap=tk.WORD, padx=10, pady=10)
        advanced_text.pack(fill=tk.BOTH, expand=True)
        advanced_content = self.help_manager.get_features_advanced()
        advanced_text.insert(tk.END, advanced_content)
        advanced_text.config(state=tk.DISABLED)
        
        # 技术特性标签页
        tech_frame = ttk.Frame(notebook)
        notebook.add(tech_frame, text="技术特性")
        
        tech_text = tk.Text(tech_frame, wrap=tk.WORD, padx=10, pady=10)
        tech_text.pack(fill=tk.BOTH, expand=True)
        tech_content = self.help_manager.get_features_technical()
        tech_text.insert(tk.END, tech_content)
        tech_text.config(state=tk.DISABLED)
        
        ttk.Button(features_window, text="关闭", command=features_window.destroy).pack(pady=10)
    
    def show_about(self):
        """显示关于信息"""
        about_window = tk.Toplevel(self.root)
        about_window.title("关于")
        about_window.geometry("600x700")
        about_window.resizable(True, True)
        
        # 主标题
        title_label = tk.Label(about_window, text="CAN多信号曲线图查看器", 
                              font=("Arial", 16, "bold"), fg="navy")
        title_label.pack(pady=20)
        
        # 创建滚动文本框的容器
        text_frame = ttk.Frame(about_window)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        # 创建滚动条
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 创建文本框
        text_widget = tk.Text(text_frame, wrap=tk.WORD, yscrollcommand=scrollbar.set, 
                             font=("Arial", 10), padx=15, pady=15, 
                             relief=tk.SUNKEN, borderwidth=2)
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 配置滚动条
        scrollbar.config(command=text_widget.yview)
        
        # 使用帮助管理器获取关于信息
        about_text = self.help_manager.get_about_info()
        text_widget.insert(tk.END, about_text)
        text_widget.config(state=tk.DISABLED)  # 设置为只读
        
        # 关闭按钮
        ttk.Button(about_window, text="关闭", command=about_window.destroy).pack(pady=10)
    
    def load_file(self):
        """加载ASC文件"""
        file_path = filedialog.askopenfilename(
            title="选择ASC文件",
            filetypes=[("ASC files", "*.asc"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            self.status_label.config(text="正在加载文件...")
            self.root.update()
            
            reader = SimpleASCReader()
            self.messages = reader.read_file(file_path)
            
            if not self.messages:
                messagebox.showerror("错误", "未找到CAN消息")
                return
            
            # 更新文件标签
            self.file_label.config(text=f"已加载: {os.path.basename(file_path)}")
            
            # 统计CAN ID
            can_id_stats = defaultdict(int)
            for msg in self.messages:
                can_id_stats[msg['can_id']] += 1
            
            # 清理缓存（数据变化了）
            self.frame_stats_cache.clear()
            self.signal_data_cache.clear()
            self.dropped_frames_cache.clear()
            
            # 统计扩展帧信息
            frame_type_info = {}
            for msg in self.messages:
                can_id = msg['can_id']
                if can_id not in frame_type_info:
                    is_extended = msg.get('is_extended', can_id > 0x7FF)
                    frame_type_info[can_id] = is_extended
            
            # 更新CAN ID选择框（显示帧类型）
            can_ids = []
            for can_id in sorted(can_id_stats.keys()):
                is_extended = frame_type_info.get(can_id, can_id > 0x7FF)
                if is_extended:
                    can_ids.append(f"0x{can_id:X} (扩展帧)")
                else:
                    can_ids.append(f"0x{can_id:X} (标准帧)")
            
            self.can_id_combo['values'] = can_ids
            
            if can_ids:
                self.can_id_combo.current(0)
            
            self.status_label.config(text=f"已加载 {len(self.messages)} 条消息，{len(can_id_stats)} 个CAN ID")
            
            # 更新时间范围显示
            if self.messages:
                min_time = min(msg['timestamp'] for msg in self.messages)
                max_time = max(msg['timestamp'] for msg in self.messages)
                self.time_start_var.set(f"{min_time:.3f}")
                self.time_end_var.set(f"{max_time:.3f}")
                self.current_time_range = (min_time, max_time)
                
            # 清空缓存
            self.frame_stats_cache.clear()
            self.signal_data_cache.clear()
            
        except Exception as e:
            messagebox.showerror("错误", f"加载文件失败: {e}")
            self.status_label.config(text="加载文件失败")
    
    def add_signal(self):
        """添加信号到列表"""
        if not self.messages:
            messagebox.showwarning("警告", "请先加载ASC文件")
            return
        
        can_id_str = self.can_id_var.get()
        if not can_id_str:
            messagebox.showwarning("警告", "请选择CAN ID")
            return
        
        try:
            # 从下拉框文本中提取CAN ID（支持带帧类型标识的格式）
            if "0x" in can_id_str:
                # 提取0x后面的十六进制数字，忽略后面的帧类型标识
                hex_part = can_id_str.split("(")[0].strip()  # 移除帧类型标识
                can_id = int(hex_part, 16)
            else:
                can_id = int(can_id_str, 16)
                
            start_bit = int(self.start_bit_var.get())
            length = int(self.length_var.get())
            factor = float(self.factor_var.get())
            offset = float(self.offset_var.get())
            signed = self.signed_var.get()
            endian = self.endian_var.get()
            name = self.signal_name_var.get() or f"信号{len(self.signal_configs)+1}"
            
            # 检查信号是否有效
            test_messages = [msg for msg in self.messages if msg['can_id'] == can_id]
            if not test_messages:
                messagebox.showwarning("警告", f"没有找到CAN ID {can_id_str}的消息")
                return
            
            if start_bit + length > 64:
                messagebox.showwarning("警告", "信号位置超出CAN数据范围(64位)")
                return
            
            # 添加信号配置
            signal_config = {
                'name': name,
                'can_id': can_id,
                'start_bit': start_bit,
                'length': length,
                'factor': factor,
                'offset': offset,
                'signed': signed,
                'endian': endian,
                'color': self.colors[len(self.signal_configs) % len(self.colors)]
            }
            
            self.signal_configs.append(signal_config)
            
            # 计算帧统计信息
            frame_stats = self.calculate_frame_stats(can_id)
            
            # 更新列表显示（包含丢帧信息）
            endian_text = "大端" if endian == "big" else "小端"
            if frame_stats:
                period_text = f"{frame_stats['period_ms']:.1f}ms"
                drop_text = f"{frame_stats['dropped_frames']}帧({frame_stats['drop_rate']:.1f}%)"
                display_text = f"{name} | {can_id_str} | {start_bit}-{start_bit+length-1}位 | {endian_text} | 周期:{period_text} | 丢帧:{drop_text}"
            else:
                display_text = f"{name} | {can_id_str} | {start_bit}-{start_bit+length-1}位 | {endian_text} | 统计:计算失败"
            
            self.signal_listbox.insert(tk.END, display_text)
            
            # 自动更新信号名称
            self.signal_name_var.set(f"信号{len(self.signal_configs)+1}")
            
            self.status_label.config(text=f"已添加信号: {name}")
            
            # 自动更新图表
            self.update_chart()
            
        except ValueError as e:
            messagebox.showerror("错误", f"配置参数无效: {e}")
    
    def remove_signal(self):
        """删除选中的信号"""
        selection = self.signal_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请选择要删除的信号")
            return
        
        index = selection[0]
        self.signal_configs.pop(index)
        self.signal_listbox.delete(index)
        
        self.update_chart()
        self.status_label.config(text="已删除信号")
    
    def show_signal_stats(self):
        """显示选中信号的详细统计信息"""
        selection = self.signal_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请选择要查看统计的信号")
            return
        
        index = selection[0]
        if index >= len(self.signal_configs):
            return
        
        config = self.signal_configs[index]
        can_id = config['can_id']
        
        # 计算详细统计
        frame_stats = self.calculate_frame_stats(can_id)
        if not frame_stats:
            messagebox.showerror("错误", "无法计算统计信息")
            return
        
        # 创建统计信息窗口
        stats_window = tk.Toplevel(self.root)
        # 获取帧类型信息
        frame_type = "未知"
        for msg in self.messages:
            if msg['can_id'] == can_id:
                if 'is_extended' in msg:
                    frame_type = "扩展帧" if msg['is_extended'] else "标准帧"
                else:
                    frame_type = "扩展帧" if can_id > 0x7FF else "标准帧"
                break
        
        stats_window.title(f"信号统计 - {config['name']} (0x{can_id:X})")
        stats_window.geometry("400x300")
        stats_window.resizable(False, False)
        
        # 统计信息文本
        stats_text = f"""
🎯 信号信息:
  • 信号名称: {config['name']}
  • CAN ID: 0x{can_id:X} ({frame_type})
  • 位位置: {config['start_bit']}-{config['start_bit']+config['length']-1}
  • 字节序: {'大端' if config['endian'] == 'big' else '小端'}

📊 帧统计:
  • 估算周期: {frame_stats['period_ms']:.2f} ms
  • 实际帧数: {frame_stats['total_frames']} 帧
  • 期望帧数: {frame_stats['expected_frames']} 帧
  • 丢失帧数: {frame_stats['dropped_frames']} 帧
  • 丢帧率: {frame_stats['drop_rate']:.2f}%
  • 时间跨度: {frame_stats['time_span']:.3f} 秒

💡 分析建议:
"""
        
        # 添加分析建议
        if frame_stats['drop_rate'] < 1:
            stats_text += "  ✅ 通信质量良好，丢帧率很低"
        elif frame_stats['drop_rate'] < 5:
            stats_text += "  ⚠️ 存在少量丢帧，建议检查网络负载"
        else:
            stats_text += "  ❌ 丢帧率较高，可能存在网络问题"
        
        if frame_stats['period_ms'] < 10:
            stats_text += "\n  📈 高频信号，注意处理性能"
        elif frame_stats['period_ms'] > 1000:
            stats_text += "\n  📉 低频信号，适合状态监控"
        
        # 显示统计信息
        text_widget = tk.Text(stats_window, wrap=tk.WORD, padx=10, pady=10)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_widget.insert(tk.END, stats_text)
        text_widget.config(state=tk.DISABLED)
        
        # 关闭按钮
        ttk.Button(stats_window, text="关闭", command=stats_window.destroy).pack(pady=10)
    
    def clear_signals(self):
        """清除所有信号"""
        self.signal_configs.clear()
        self.signal_listbox.delete(0, tk.END)
        
        # 清理缓存
        self.frame_stats_cache.clear()
        self.signal_data_cache.clear()
        self.dropped_frames_cache.clear()
        
        self.figure.clear()
        self.canvas.draw()
        self.status_label.config(text="已清除所有信号")
    
    def extract_signal_value(self, data_bytes, start_bit, length, factor=1.0, offset=0.0, signed=False, endian="big"):
        """提取信号值 - 高性能优化版本"""
        try:
            # 优化：预计算常用值
            total_bits = len(data_bytes) << 3  # 位运算替代乘法
            if start_bit + length > total_bits:
                return None, None
            
            # 优化：使用位运算进行字节组合
            if endian == "big":
                data_int = 0
                for byte in data_bytes:
                    data_int = (data_int << 8) | byte
                right_start_bit = total_bits - start_bit - length
            else:
                data_int = 0
                for i, byte in enumerate(data_bytes):
                    data_int |= byte << (i << 3)  # 位运算替代乘法
                right_start_bit = start_bit
            
            # 优化：使用位运算提取信号
            mask = (1 << length) - 1
            raw_value = (data_int >> right_start_bit) & mask
            
            # 优化：有符号数处理
            if signed and length < 32:
                sign_bit = 1 << (length - 1)
                if raw_value & sign_bit:
                    raw_value -= 1 << length
            
            # 优化：避免不必要的计算
            if factor == 1.0 and offset == 0.0:
                physical_value = float(raw_value)
            else:
                physical_value = raw_value * factor + offset
            
            return raw_value, physical_value
            
        except Exception as e:
            return None, None
    
    def apply_time_range(self):
        """应用时间范围"""
        try:
            start_time = float(self.time_start_var.get())
            end_time = float(self.time_end_var.get())
            
            if start_time >= end_time:
                messagebox.showwarning("警告", "开始时间必须小于结束时间")
                return
            
            self.current_time_range = (start_time, end_time)
            self.update_chart()
            self.status_label.config(text=f"已应用时间范围: {start_time:.3f}s - {end_time:.3f}s")
            
        except ValueError:
            messagebox.showerror("错误", "时间范围格式无效")
    
    def reset_time_range(self):
        """重置时间范围"""
        if self.messages:
            min_time = min(msg['timestamp'] for msg in self.messages)
            max_time = max(msg['timestamp'] for msg in self.messages)
            self.time_start_var.set(f"{min_time:.3f}")
            self.time_end_var.set(f"{max_time:.3f}")
            self.current_time_range = (min_time, max_time)
            self.update_chart()
            self.status_label.config(text="已重置时间范围")
    
    def on_mouse_press(self, event):
        """鼠标按下事件，开始拖拽或设置测量点"""
        if not event.inaxes:
            return
        
        # 测量模式下的点击处理
        if self.measurement_mode.get() and event.button == 1:
            self.add_measurement_point(event)
            return
        
        # 拖拽模式
        if event.button == 1:
            # 记录拖拽开始状态
            self.dragging = True
            self.drag_start_pos = (event.xdata, event.ydata)
            self.drag_axis = event.inaxes
            
            # 改变鼠标光标为移动样式
            self.canvas.get_tk_widget().config(cursor="fleur")
        
    def on_mouse_move(self, event):
        """鼠标移动事件处理，包括拖拽和十字线显示"""
        # 处理拖拽
        if self.dragging:
            self.handle_drag(event)
            return
        
        # 测量模式下不显示十字线
        if self.measurement_mode.get():
            return
        
        # 处理十字线显示
        if self.crosshair_enabled.get() and event.inaxes:
            self.update_crosshair(event)
    
    def handle_drag(self, event):
        """处理拖拽操作"""
        if not event.inaxes or not self.drag_start_pos:
            return
        
        # 只有在同一个轴内拖拽才有效
        if event.inaxes != self.drag_axis:
            return
        
        # 控制重绘频率，避免过于频繁的更新
        import time
        current_time = time.time()
        if current_time - self.last_drag_time < 0.05:  # 进一步降低到20fps，更流畅
            return
        self.last_drag_time = current_time
        
        # 计算Y轴移动距离
        if event.ydata is None or self.drag_start_pos[1] is None:
            return
        
        y_delta = event.ydata - self.drag_start_pos[1]
        
        # 避免微小移动导致的抖动
        if abs(y_delta) < 0.005:  # 增加阈值，减少微小抖动
            return
        
        # 获取当前Y轴范围
        ylim = self.drag_axis.get_ylim()
        y_range = ylim[1] - ylim[0]
        
        # 移动Y轴（向上拖拽图表向下移动，向下拖拽图表向上移动）
        new_ylim = [ylim[0] - y_delta, ylim[1] - y_delta]
        self.drag_axis.set_ylim(new_ylim)
        
        # 更新拖拽起始位置
        self.drag_start_pos = (event.xdata, event.ydata)
        
        # 防止重复的更新请求
        if not self.drag_update_pending:
            self.drag_update_pending = True
            # 使用after方法延迟更新，避免频繁重绘
            self.root.after_idle(self._delayed_drag_update)
    
    def update_crosshair(self, event):
        """更新十字线和数据显示"""
        if not event.xdata or not event.ydata:
            return
        
        x_pos = event.xdata
        
        # 清除之前的十字线和标注
        self.clear_crosshair()
        
        # 为每个子图添加垂直线和数据标注
        if hasattr(self, 'axes_list') and self.axes_list:
            for ax in self.axes_list:
                self.add_crosshair_to_axis(ax, x_pos)
        elif hasattr(self, 'current_ax') and self.current_ax:
            self.add_crosshair_to_axis(self.current_ax, x_pos)
        
        # 重绘画布
        self.canvas.draw_idle()
    
    def add_crosshair_to_axis(self, ax, x_pos):
        """为指定轴添加十字线和数据标注"""
        # 添加垂直线
        ylim = ax.get_ylim()
        vline = ax.axvline(x_pos, color='red', linestyle='--', alpha=0.7, linewidth=1)
        self.vlines[ax] = vline
        
        # 查找最接近的数据点并显示值
        for line in ax.lines:
            if line == vline:  # 跳过刚添加的垂直线
                continue
            
            xdata = line.get_xdata()
            ydata = line.get_ydata()
            
            if len(xdata) == 0:
                continue
            
            # 找到最接近x_pos的数据点
            idx = None
            min_dist = float('inf')
            for i, x_val in enumerate(xdata):
                dist = abs(x_val - x_pos)
                if dist < min_dist:
                    min_dist = dist
                    idx = i
            
            if idx is not None and min_dist < (max(xdata) - min(xdata)) * 0.01:  # 只有在合理范围内才显示
                x_val = xdata[idx]
                y_val = ydata[idx]
                
                # 添加数据标注
                annotation = ax.annotate(f'({x_val:.3f}, {y_val:.3f})',
                                       xy=(x_val, y_val),
                                       xytext=(10, 10),
                                       textcoords='offset points',
                                       bbox=dict(boxstyle='round,pad=0.3', 
                                               facecolor='yellow', 
                                               alpha=0.8),
                                       fontsize=9,
                                       ha='left')
                
                if ax not in self.data_annotations:
                    self.data_annotations[ax] = []
                self.data_annotations[ax].append(annotation)
                break  # 只显示第一条线的数据
    
    def clear_crosshair(self):
        """清除所有十字线和数据标注"""
        # 清除垂直线
        for ax, vline in self.vlines.items():
            if vline in ax.lines:
                vline.remove()
        self.vlines.clear()
        
        # 清除数据标注
        for ax, annotations in self.data_annotations.items():
            for annotation in annotations:
                annotation.remove()
        self.data_annotations.clear()
    
    def toggle_crosshair(self):
        """切换十字线显示状态"""
        if not self.crosshair_enabled.get():
            self.clear_crosshair()
            self.canvas.draw_idle()
    
    def toggle_measurement_mode(self):
        """切换测量模式"""
        if self.measurement_mode.get():
            # 进入测量模式，清除现有测量
            self.clear_measurement()
            self.clear_crosshair()  # 也清除十字线
            self.status_label.config(text="测量模式：左键点击两个点进行测量，右键清除")
        else:
            # 退出测量模式
            self.clear_measurement()
            self.status_label.config(text="已退出测量模式")
    
    def add_measurement_point(self, event):
        """添加测量点"""
        if not event.xdata or not event.ydata:
            return
        
        x_pos = event.xdata
        y_pos = event.ydata
        
        # 添加测量点
        if len(self.measurement_points) >= 2:
            # 如果已有两个点，清除重新开始
            self.clear_measurement()
        
        self.measurement_points.append((x_pos, y_pos))
        
        # 绘制测量线和标注
        self.update_measurement_display()
    
    def update_measurement_display(self):
        """更新测量显示"""
        # 清除之前的测量显示
        self.clear_measurement_display()
        
        if not self.measurement_points:
            return
        
        # 为每个子图添加测量线
        axes_to_update = self.axes_list if self.axes_list else [self.current_ax] if self.current_ax else []
        
        for ax in axes_to_update:
            if ax is None:
                continue
            
            # 绘制第一个点
            if len(self.measurement_points) >= 1:
                x1, y1 = self.measurement_points[0]
                ylim = ax.get_ylim()
                
                # 垂直线1
                line1 = ax.axvline(x1, color='green', linestyle='-', alpha=0.8, linewidth=2)
                if ax not in self.measurement_lines:
                    self.measurement_lines[ax] = []
                self.measurement_lines[ax].append(line1)
                
                # 标注点1
                annotation1 = ax.annotate(f'P1({x1:.3f})',
                                        xy=(x1, ylim[1]),
                                        xytext=(5, -5),
                                        textcoords='offset points',
                                        bbox=dict(boxstyle='round,pad=0.3', 
                                                facecolor='green', 
                                                alpha=0.8),
                                        fontsize=9,
                                        ha='left')
                
                if ax not in self.measurement_annotations:
                    self.measurement_annotations[ax] = []
                self.measurement_annotations[ax].append(annotation1)
            
            # 绘制第二个点和测量结果
            if len(self.measurement_points) >= 2:
                x2, y2 = self.measurement_points[1]
                ylim = ax.get_ylim()
                
                # 垂直线2
                line2 = ax.axvline(x2, color='blue', linestyle='-', alpha=0.8, linewidth=2)
                self.measurement_lines[ax].append(line2)
                
                # 标注点2
                annotation2 = ax.annotate(f'P2({x2:.3f})',
                                        xy=(x2, ylim[1]),
                                        xytext=(5, -5),
                                        textcoords='offset points',
                                        bbox=dict(boxstyle='round,pad=0.3', 
                                                facecolor='blue', 
                                                alpha=0.8),
                                        fontsize=9,
                                        ha='left')
                self.measurement_annotations[ax].append(annotation2)
                
                # 计算时间差
                time_diff = abs(x2 - x1)
                
                # 在两线中间显示时间差
                mid_x = (x1 + x2) / 2
                mid_y = (ylim[0] + ylim[1]) / 2
                
                diff_annotation = ax.annotate(f'Δt = {time_diff:.3f}s',
                                            xy=(mid_x, mid_y),
                                            xytext=(0, 0),
                                            textcoords='offset points',
                                            bbox=dict(boxstyle='round,pad=0.5', 
                                                    facecolor='yellow', 
                                                    alpha=0.9),
                                            fontsize=11,
                                            ha='center',
                                            weight='bold')
                self.measurement_annotations[ax].append(diff_annotation)
                
                # 连接线
                connection_line = ax.plot([x1, x2], [mid_y, mid_y], 
                                        color='red', linestyle='--', alpha=0.7, linewidth=1)[0]
                self.measurement_lines[ax].append(connection_line)
        
        # 更新状态显示
        if len(self.measurement_points) == 1:
            self.status_label.config(text="已设置第一个测量点，请点击第二个点")
        elif len(self.measurement_points) == 2:
            time_diff = abs(self.measurement_points[1][0] - self.measurement_points[0][0])
            self.status_label.config(text=f"测量完成：时间差 = {time_diff:.6f}秒")
        
        # 重绘画布
        self.canvas.draw_idle()
    
    def clear_measurement_display(self):
        """清除测量显示元素"""
        # 清除测量线
        for ax, lines in self.measurement_lines.items():
            for line in lines:
                if hasattr(line, 'remove'):
                    line.remove()
        self.measurement_lines.clear()
        
        # 清除测量标注
        for ax, annotations in self.measurement_annotations.items():
            for annotation in annotations:
                if hasattr(annotation, 'remove'):
                    annotation.remove()
        self.measurement_annotations.clear()
    
    def clear_measurement(self):
        """清除所有测量"""
        self.measurement_points.clear()
        self.clear_measurement_display()
        self.canvas.draw_idle()
        if self.measurement_mode.get():
            self.status_label.config(text="测量模式：左键点击两个点进行测量，右键清除")
    
    def _delayed_drag_update(self):
        """延迟的拖拽更新，减少闪烁"""
        try:
            self.canvas.draw_idle()
        finally:
            self.drag_update_pending = False
    
    def update_x_axis_time_format(self, ax):
        """更新X轴时间格式显示"""
        if not ax:
            return
        
        try:
            # 获取当前X轴范围
            xlim = ax.get_xlim()
            time_range = xlim[1] - xlim[0]
            
            # 根据时间范围选择合适的显示格式
            if time_range > 60:  # 超过60秒，显示分:秒
                from matplotlib.ticker import FuncFormatter
                def time_formatter(x, pos):
                    minutes = int(x // 60)
                    seconds = x % 60
                    return f"{minutes}:{seconds:05.2f}"
                ax.xaxis.set_major_formatter(FuncFormatter(time_formatter))
            elif time_range > 10:  # 10-60秒，显示秒数到小数点后1位
                from matplotlib.ticker import FuncFormatter
                def time_formatter(x, pos):
                    return f"{x:.1f}s"
                ax.xaxis.set_major_formatter(FuncFormatter(time_formatter))
            else:  # 小于10秒，显示到小数点后3位
                from matplotlib.ticker import FuncFormatter
                def time_formatter(x, pos):
                    return f"{x:.3f}s"
                ax.xaxis.set_major_formatter(FuncFormatter(time_formatter))
            
            # 设置X轴标签
            ax.set_xlabel('时间')
            
        except Exception as e:
            print(f"更新X轴时间格式失败: {e}")
    
    def on_mouse_scroll(self, event):
        """鼠标滚轮事件，用于缩放图表"""
        if not event.inaxes:
            return
        
        # 获取当前鼠标位置
        x_center = event.xdata
        y_center = event.ydata
        
        if x_center is None or y_center is None:
            return
        
        # 获取当前轴的范围
        xlim = event.inaxes.get_xlim()
        ylim = event.inaxes.get_ylim()
        
        # 计算缩放因子 (向上滚动放大，向下滚动缩小)
        if event.button == 'up':
            scale_factor = 1 / self.zoom_factor
        elif event.button == 'down':
            scale_factor = self.zoom_factor
        else:
            return
        
        # 计算新的范围，以鼠标位置为中心缩放
        x_range = xlim[1] - xlim[0]
        y_range = ylim[1] - ylim[0]
        
        new_x_range = x_range * scale_factor
        new_y_range = y_range * scale_factor
        
        # 计算新的边界，保持鼠标位置不变
        x_ratio = (x_center - xlim[0]) / x_range
        y_ratio = (y_center - ylim[0]) / y_range
        
        new_xlim = [
            x_center - new_x_range * x_ratio,
            x_center + new_x_range * (1 - x_ratio)
        ]
        new_ylim = [
            y_center - new_y_range * y_ratio,
            y_center + new_y_range * (1 - y_ratio)
        ]
        
        # 应用新的范围
        event.inaxes.set_xlim(new_xlim)
        event.inaxes.set_ylim(new_ylim)
        
        # 如果是子图模式，同步所有子图的x轴
        if self.subplot_mode_active and self.axes_list and len(self.axes_list) > 1:
            for ax in self.axes_list:
                if ax != event.inaxes:
                    ax.set_xlim(new_xlim)
        
        # 更新X轴时间标签格式
        self.update_x_axis_time_format(event.inaxes)
        if self.subplot_mode_active and self.axes_list:
            for ax in self.axes_list:
                if ax != event.inaxes:
                    self.update_x_axis_time_format(ax)
        
        # 更新时间范围显示
        if hasattr(self, 'time_start_var') and hasattr(self, 'time_end_var'):
            self.time_start_var.set(f"{new_xlim[0]:.3f}")
            self.time_end_var.set(f"{new_xlim[1]:.3f}")
            self.current_time_range = new_xlim
        
        # 重绘画布
        self.canvas.draw_idle()
    
    def on_mouse_release(self, event):
        """鼠标释放事件，用于检测缩放操作和结束拖拽"""
        # 结束拖拽状态
        if self.dragging:
            self.dragging = False
            self.drag_start_pos = None
            self.drag_axis = None
            self.drag_update_pending = False
            # 恢复默认鼠标光标
            self.canvas.get_tk_widget().config(cursor="")
            # 最终重绘确保显示正确
            self.canvas.draw()  # 使用立即重绘确保最终状态正确
            return
        
        # 测量模式下右键清除测量
        if self.measurement_mode.get() and event.button == 3:  # 右键
            self.clear_measurement()
            return
        
        # 处理子图x轴同步（原有逻辑）
        if not self.subplot_mode_active or not self.axes_list or len(self.axes_list) <= 1:
            return
        
        # 检查是否在某个子图内
        if event.inaxes and event.inaxes in self.axes_list:
            # 获取当前子图的x轴范围
            xlim = event.inaxes.get_xlim()
            
            # 同步所有其他子图的x轴
            for ax in self.axes_list:
                if ax != event.inaxes:
                    ax.set_xlim(xlim)
                    self.update_x_axis_time_format(ax)
            
            # 更新当前轴的时间格式
            self.update_x_axis_time_format(event.inaxes)
            
            # 更新时间范围显示
            self.time_start_var.set(f"{xlim[0]:.3f}")
            self.time_end_var.set(f"{xlim[1]:.3f}")
            self.current_time_range = xlim
            
            # 重绘画布
            self.canvas.draw_idle()
    
    def sync_subplot_xlims(self, source_ax):
        """同步所有子图的x轴范围"""
        if not self.subplot_mode_active or not self.axes_list:
            return
        
        xlim = source_ax.get_xlim()
        for ax in self.axes_list:
            if ax != source_ax:
                ax.set_xlim(xlim)
    
    def update_chart(self):
        """更新图表 - 性能优化版本"""
        import time
        current_time = time.time()
        
        # 防抖动：如果更新太频繁，跳过此次更新
        if current_time - self.last_update_time < 0.1:  # 100ms防抖
            return
        
        self.last_update_time = current_time
        
        if not self.signal_configs:
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, '请添加信号来显示曲线图', 
                   ha='center', va='center', transform=ax.transAxes, fontsize=16)
            self.canvas.draw_idle()  # 使用draw_idle而不是draw
            return
        
        try:
            self.figure.clear()
            
            # 确定时间范围
            if self.current_time_range:
                time_start, time_end = self.current_time_range
            else:
                time_start = float(self.time_start_var.get()) if self.time_start_var.get() else None
                time_end = float(self.time_end_var.get()) if self.time_end_var.get() else None
            
            # 子图模式
            subplot_mode = self.subplot_mode_var.get()
            n_signals = len(self.signal_configs)
            
            # 更新子图模式状态
            self.subplot_mode_active = subplot_mode
            self.axes_list = []
            
            if subplot_mode and n_signals > 1:
                # 创建多个子图，共享x轴
                axes = []
                first_ax = None
                for i in range(n_signals):
                    if i == 0:
                        ax = self.figure.add_subplot(n_signals, 1, i+1)
                        first_ax = ax
                    else:
                        # 与第一个子图共享x轴
                        ax = self.figure.add_subplot(n_signals, 1, i+1, sharex=first_ax)
                    axes.append(ax)
                    self.axes_list.append(ax)
            else:
                # 单个图表
                ax = self.figure.add_subplot(111)
                axes = [ax] * n_signals
                self.axes_list = [ax]
                self.subplot_mode_active = False
            
            # 存储当前轴用于十字线功能
            self.current_ax = self.axes_list[0] if self.axes_list else None
            
            total_points = 0
            all_timestamps = []
            
            for i, config in enumerate(self.signal_configs):
                # 优化：使用缓存的信号数据
                signal_cache_key = f"{config['can_id']}_{config['start_bit']}_{config['length']}_{config['endian']}"
                
                if signal_cache_key in self.signal_data_cache:
                    timestamps, values = self.signal_data_cache[signal_cache_key]
                else:
                    # 过滤对应CAN ID的消息（优化：一次性过滤）
                    filtered_messages = [msg for msg in self.messages if msg['can_id'] == config['can_id']]
                    
                    if not filtered_messages:
                        continue
                    
                    # 优化：批量提取信号数据
                    timestamps = []
                    values = []
                    
                    for msg in filtered_messages:
                        raw, physical = self.extract_signal_value(
                            msg['data'], 
                            config['start_bit'], 
                            config['length'], 
                            config['factor'], 
                            config['offset'], 
                            config['signed'],
                            config['endian']
                        )
                        if physical is not None:
                            timestamps.append(msg['timestamp'])
                            values.append(physical)
                    
                    # 缓存信号数据
                    self.signal_data_cache[signal_cache_key] = (timestamps, values)
                
                # 应用时间范围过滤（优化：使用列表推导式）
                if time_start is not None or time_end is not None:
                    filtered_data = [
                        (ts, val) for ts, val in zip(timestamps, values)
                        if (time_start is None or ts >= time_start) and 
                           (time_end is None or ts <= time_end)
                    ]
                    if filtered_data:
                        plot_timestamps, plot_values = zip(*filtered_data)
                    else:
                        plot_timestamps, plot_values = [], []
                else:
                    plot_timestamps, plot_values = timestamps, values
                
                if plot_timestamps:
                    current_ax = axes[i if subplot_mode else 0]
                    
                    # 绘制正常数据曲线
                    line = current_ax.plot(plot_timestamps, plot_values, 
                           color=config['color'], 
                           linewidth=1.5, 
                           marker='o', 
                           markersize=2,
                           label=f"{config['name']} (0x{config['can_id']:X})")
                    
                    # 添加丢帧点显示（优化：只在需要时计算）
                    if self.show_dropped_frames_var.get():
                        # 使用缓存的帧统计
                        frame_stats = self.calculate_frame_stats(config['can_id'], use_cache=True)
                        if frame_stats and frame_stats['period_ms'] > 0:
                            period_seconds = frame_stats['period_ms'] / 1000.0
                            
                            # 使用缓存的丢帧检测
                            dropped_times = self.detect_dropped_frame_positions(
                                config['can_id'], period_seconds, use_cache=True)
                            
                            if dropped_times:
                                # 优化：时间范围过滤
                                if time_start is not None or time_end is not None:
                                    filtered_dropped_times = [
                                        dt for dt in dropped_times
                                        if (time_start is None or dt >= time_start) and 
                                           (time_end is None or dt <= time_end)
                                    ]
                                else:
                                    filtered_dropped_times = dropped_times
                                
                                if filtered_dropped_times:
                                    # 优化：批量插值计算
                                    interpolated_values = self.interpolate_signal_at_dropped_frames(
                                        timestamps, values, filtered_dropped_times)
                                    
                                    # 绘制丢帧点（优化：减少标记数量以提高性能）
                                    if len(filtered_dropped_times) <= 1000:  # 限制标记数量
                                        current_ax.scatter(filtered_dropped_times, interpolated_values,
                                                         color='red', s=50, marker='X', 
                                                         alpha=0.8, zorder=5,
                                                         label=f'丢帧点({len(filtered_dropped_times)}个)')
                                    else:
                                        # 对于大量丢帧点，采样显示
                                        step = len(filtered_dropped_times) // 500
                                        sampled_times = filtered_dropped_times[::step]
                                        sampled_values = interpolated_values[::step]
                                        current_ax.scatter(sampled_times, sampled_values,
                                                         color='red', s=50, marker='X', 
                                                         alpha=0.8, zorder=5,
                                                         label=f'丢帧点(约{len(filtered_dropped_times)}个)')
                    
                    total_points += len(plot_timestamps)
                    all_timestamps.extend(plot_timestamps)
                    
                    # 子图模式下的标题和标签
                    if subplot_mode:
                        current_ax.set_title(f"{config['name']} (0x{config['can_id']:X})", fontsize=10)
                        current_ax.set_ylabel('值', fontsize=9)
                        
                        # 只在最后一个子图显示x轴标签
                        if i == n_signals - 1:
                            current_ax.set_xlabel('时间 (秒)')
                        else:
                            current_ax.set_xticklabels([])
                        
                        # 添加统计信息到标题
                        if values:
                            min_val = min(values)
                            max_val = max(values)
                            avg_val = sum(values) / len(values)
                            current_ax.text(0.02, 0.98, f'范围: {min_val:.2f}~{max_val:.2f}, 均值: {avg_val:.2f}',
                                          transform=current_ax.transAxes, fontsize=8, verticalalignment='top',
                                          bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
                    
                    total_points += len(timestamps)
                    all_timestamps.extend(timestamps)
                    
                    # 网格
                    if self.show_grid_var.get():
                        current_ax.grid(True, alpha=0.3)
            
            # 设置图表属性
            if not subplot_mode:
                ax.set_xlabel('时间 (秒)')
                ax.set_ylabel('信号值')
                ax.set_title('CAN多信号曲线图')
                
                if self.show_legend_var.get() and self.signal_configs:
                    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            else:
                # 子图模式的总标题
                self.figure.suptitle('CAN信号子图显示', fontsize=14)
            
            # 同步所有子图的x轴范围（子图模式下）
            if subplot_mode and all_timestamps and len(self.axes_list) > 1:
                # 确定时间范围
                if time_start is not None and time_end is not None:
                    min_time, max_time = time_start, time_end
                else:
                    min_time = min(all_timestamps)
                    max_time = max(all_timestamps)
                
                # 同步所有子图的x轴
                for ax in self.axes_list:
                    ax.set_xlim(min_time, max_time)
                    # 更新每个子图的X轴时间格式
                    self.update_x_axis_time_format(ax)
            
            # 如果是单图模式，也更新时间格式
            if not subplot_mode and ax:
                self.update_x_axis_time_format(ax)
            
            # 调整布局
            self.figure.tight_layout()
            
            # 更新画布 - 使用idle模式提升性能
            self.canvas.draw_idle()
            
            # 更新状态信息
            range_info = ""
            if self.current_time_range:
                range_info = f" | 时间范围: {self.current_time_range[0]:.3f}s-{self.current_time_range[1]:.3f}s"
            
            mode_info = "子图模式" if subplot_mode else "叠加模式"
            self.status_label.config(text=f"已绘制 {len(self.signal_configs)} 个信号 ({mode_info})，共 {total_points} 个数据点{range_info}")
            
        except Exception as e:
            messagebox.showerror("错误", f"更新图表失败: {e}")
    
    def init_dbc_plugin(self):
        """初始化DBC插件"""
        try:
            from dbc_plugin import DBCPlugin
            
            print("🔌 初始化DBC插件...")
            # 创建DBC插件实例
            self.dbc_plugin = DBCPlugin(self)
            
            # 直接在add_frame中添加DBC UI
            if hasattr(self, 'add_frame') and self.add_frame:
                # 在添加信号frame中添加DBC UI
                self.dbc_frame = self.dbc_plugin.create_dbc_ui(self.add_frame)
                print("✅ DBC插件UI已添加到界面")
            else:
                print("⚠️ 未找到添加信号的frame")
                
            print("✅ DBC插件初始化成功")
            
        except ImportError as e:
            print(f"⚠️ DBC插件加载失败: {e}")
            print("💡 DBC功能将不可用")
        except Exception as e:
            print(f"❌ DBC插件初始化失败: {e}")
            import traceback
            traceback.print_exc()
        except Exception as e:
            print(f"❌ DBC插件初始化失败: {e}")
            import traceback
            traceback.print_exc()

def main():
    """主函数"""
    root = tk.Tk()
    app = MultiSignalChartViewer(root)
    
    root.mainloop()

if __name__ == "__main__":
    main()