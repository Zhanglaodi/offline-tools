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

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from simple_asc_reader import SimpleASCReader

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

class MultiSignalChartViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("CAN多信号曲线图查看器")
        self.root.geometry("1400x900")
        
        # 数据存储
        self.messages = []
        self.signal_configs = []  # 存储多个信号配置
        self.colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan']
        
        # 默认信号配置
        self.signal_presets = {
            "第1字节 (0-7位)": {"start": 0, "length": 8, "factor": 1.0, "offset": 0.0, "signed": False, "endian": "big"},
            "前2字节转速 (0-15位)": {"start": 0, "length": 16, "factor": 0.25, "offset": 0.0, "signed": False, "endian": "big"},
            "温度信号 (16-23位)": {"start": 16, "length": 8, "factor": 1.0, "offset": -40.0, "signed": False, "endian": "big"},
            "电压信号 (0-11位)": {"start": 0, "length": 12, "factor": 0.01, "offset": 0.0, "signed": False, "endian": "big"},
            "有符号温度 (24-31位)": {"start": 24, "length": 8, "factor": 0.5, "offset": 0.0, "signed": True, "endian": "big"},
            "小端16位信号 (0-15位)": {"start": 0, "length": 16, "factor": 1.0, "offset": 0.0, "signed": False, "endian": "little"},
        }
        
        # 创建界面
        self.create_widgets()
    
    def create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 左侧控制面板
        control_frame = ttk.LabelFrame(main_frame, text="控制面板", padding=10)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # 文件选择
        file_frame = ttk.Frame(control_frame)
        file_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Button(file_frame, text="选择ASC文件", command=self.load_file).pack(fill=tk.X)
        self.file_label = ttk.Label(file_frame, text="未选择文件", foreground="gray")
        self.file_label.pack(fill=tk.X, pady=(5, 0))
        
        # 信号添加区域
        add_frame = ttk.LabelFrame(control_frame, text="添加信号", padding=5)
        add_frame.pack(fill=tk.X, pady=(0, 10))
        
        # CAN ID选择
        id_frame = ttk.Frame(add_frame)
        id_frame.pack(fill=tk.X, pady=2)
        ttk.Label(id_frame, text="CAN ID:", width=8).pack(side=tk.LEFT)
        self.can_id_var = tk.StringVar()
        self.can_id_combo = ttk.Combobox(id_frame, textvariable=self.can_id_var, state="readonly", width=12)
        self.can_id_combo.pack(side=tk.RIGHT)
        
        # 预设信号
        preset_frame = ttk.Frame(add_frame)
        preset_frame.pack(fill=tk.X, pady=2)
        ttk.Label(preset_frame, text="预设:", width=8).pack(side=tk.LEFT)
        self.preset_var = tk.StringVar()
        preset_combo = ttk.Combobox(preset_frame, textvariable=self.preset_var, 
                                  values=list(self.signal_presets.keys()), state="readonly", width=12)
        preset_combo.pack(side=tk.RIGHT)
        preset_combo.bind('<<ComboboxSelected>>', self.on_preset_changed)
        
        # 信号配置
        ttk.Separator(add_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)
        
        # 起始位
        start_frame = ttk.Frame(add_frame)
        start_frame.pack(fill=tk.X, pady=2)
        ttk.Label(start_frame, text="起始位:", width=8).pack(side=tk.LEFT)
        self.start_bit_var = tk.StringVar(value="0")
        ttk.Entry(start_frame, textvariable=self.start_bit_var, width=8).pack(side=tk.RIGHT)
        
        # 长度
        length_frame = ttk.Frame(add_frame)
        length_frame.pack(fill=tk.X, pady=2)
        ttk.Label(length_frame, text="长度:", width=8).pack(side=tk.LEFT)
        self.length_var = tk.StringVar(value="8")
        ttk.Entry(length_frame, textvariable=self.length_var, width=8).pack(side=tk.RIGHT)
        
        # 系数
        factor_frame = ttk.Frame(add_frame)
        factor_frame.pack(fill=tk.X, pady=2)
        ttk.Label(factor_frame, text="系数:", width=8).pack(side=tk.LEFT)
        self.factor_var = tk.StringVar(value="1.0")
        ttk.Entry(factor_frame, textvariable=self.factor_var, width=8).pack(side=tk.RIGHT)
        
        # 偏移
        offset_frame = ttk.Frame(add_frame)
        offset_frame.pack(fill=tk.X, pady=2)
        ttk.Label(offset_frame, text="偏移:", width=8).pack(side=tk.LEFT)
        self.offset_var = tk.StringVar(value="0.0")
        ttk.Entry(offset_frame, textvariable=self.offset_var, width=8).pack(side=tk.RIGHT)
        
        # 有符号
        self.signed_var = tk.BooleanVar()
        ttk.Checkbutton(add_frame, text="有符号数", variable=self.signed_var).pack(anchor=tk.W, pady=2)
        
        # 字节序选择
        endian_frame = ttk.Frame(add_frame)
        endian_frame.pack(fill=tk.X, pady=2)
        ttk.Label(endian_frame, text="字节序:", width=8).pack(side=tk.LEFT)
        self.endian_var = tk.StringVar(value="big")
        endian_combo = ttk.Combobox(endian_frame, textvariable=self.endian_var, 
                                   values=["big", "little"], state="readonly", width=8)
        endian_combo.pack(side=tk.RIGHT)
        
        # 字节序说明
        endian_info = ttk.Label(add_frame, text="big=大端(Motorola), little=小端(Intel)", 
                               font=("Arial", 8), foreground="gray")
        endian_info.pack(anchor=tk.W, pady=(0, 2))
        
        # 信号名称
        name_frame = ttk.Frame(add_frame)
        name_frame.pack(fill=tk.X, pady=2)
        ttk.Label(name_frame, text="名称:", width=8).pack(side=tk.LEFT)
        self.signal_name_var = tk.StringVar(value="信号1")
        ttk.Entry(name_frame, textvariable=self.signal_name_var, width=8).pack(side=tk.RIGHT)
        
        # 添加按钮
        button_frame = ttk.Frame(add_frame)
        button_frame.pack(fill=tk.X, pady=(5, 0))
        ttk.Button(button_frame, text="添加信号", command=self.add_signal).pack(side=tk.LEFT, padx=(0, 5))
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
        
        self.subplot_mode_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(display_frame, text="子图模式", variable=self.subplot_mode_var,
                       command=self.update_chart).pack(anchor=tk.W)
        
        # 时间范围控制
        time_frame = ttk.LabelFrame(control_frame, text="时间范围", padding=5)
        time_frame.pack(fill=tk.X, pady=(5, 0))
        
        time_input_frame = ttk.Frame(time_frame)
        time_input_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(time_input_frame, text="开始:", width=6).pack(side=tk.LEFT)
        self.time_start_var = tk.StringVar(value="")
        self.time_start_entry = ttk.Entry(time_input_frame, textvariable=self.time_start_var, width=10)
        self.time_start_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Label(time_input_frame, text="结束:", width=6).pack(side=tk.LEFT)
        self.time_end_var = tk.StringVar(value="")
        self.time_end_entry = ttk.Entry(time_input_frame, textvariable=self.time_end_var, width=10)
        self.time_end_entry.pack(side=tk.LEFT)
        
        time_btn_frame = ttk.Frame(time_frame)
        time_btn_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(time_btn_frame, text="应用范围", command=self.apply_time_range).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(time_btn_frame, text="重置范围", command=self.reset_time_range).pack(side=tk.LEFT)
        
        # 右侧图表区域
        chart_frame = ttk.Frame(main_frame)
        chart_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 创建图表
        self.figure = Figure(figsize=(10, 8), dpi=100)
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
        
        # 状态栏
        self.status_label = ttk.Label(self.root, text="请选择ASC文件并添加信号", relief=tk.SUNKEN)
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)
    
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
            
            # 更新CAN ID选择框
            can_ids = [f"0x{can_id:X}" for can_id in sorted(can_id_stats.keys())]
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
            
        except Exception as e:
            messagebox.showerror("错误", f"加载文件失败: {e}")
            self.status_label.config(text="加载文件失败")
    
    def on_preset_changed(self, event=None):
        """预设信号改变"""
        preset_name = self.preset_var.get()
        if preset_name in self.signal_presets:
            preset = self.signal_presets[preset_name]
            self.start_bit_var.set(str(preset['start']))
            self.length_var.set(str(preset['length']))
            self.factor_var.set(str(preset['factor']))
            self.offset_var.set(str(preset['offset']))
            self.signed_var.set(preset['signed'])
            self.endian_var.set(preset['endian'])
            self.signal_name_var.set(preset_name)
    
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
            
            # 更新列表显示
            endian_text = "大端" if endian == "big" else "小端"
            display_text = f"{name} | {can_id_str} | {start_bit}-{start_bit+length-1}位 | {endian_text}"
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
    
    def clear_signals(self):
        """清除所有信号"""
        self.signal_configs.clear()
        self.signal_listbox.delete(0, tk.END)
        self.figure.clear()
        self.canvas.draw()
        self.status_label.config(text="已清除所有信号")
    
    def extract_signal_value(self, data_bytes, start_bit, length, factor=1.0, offset=0.0, signed=False, endian="big"):
        """提取信号值"""
        try:
            # 将字节转换为一个大的整数
            if endian == "big":
                # 大端：MSB在前
                data_int = 0
                for byte in data_bytes:
                    data_int = (data_int << 8) | byte
            else:
                # 小端：LSB在前
                data_int = 0
                for i, byte in enumerate(data_bytes):
                    data_int |= (byte << (i * 8))
            
            # 计算总位数
            total_bits = len(data_bytes) * 8
            
            # 检查范围
            if start_bit + length > total_bits:
                return None, None
            
            # 从右边开始计算位位置（LSB为0）
            if endian == "big":
                # 大端：从左开始的位位置转换为从右开始
                right_start_bit = total_bits - start_bit - length
            else:
                # 小端：直接使用位位置
                right_start_bit = start_bit
            
            # 创建掩码提取信号
            mask = (1 << length) - 1
            raw_value = (data_int >> right_start_bit) & mask
            
            # 处理有符号数
            if signed and length < 32:
                if raw_value >= (1 << (length-1)):
                    raw_value -= (1 << length)
            
            # 应用系数和偏移
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
    
    def on_mouse_release(self, event):
        """鼠标释放事件，用于检测缩放操作"""
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
        """更新图表"""
        if not self.signal_configs:
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, '请添加信号来显示曲线图', 
                   ha='center', va='center', transform=ax.transAxes, fontsize=16)
            self.canvas.draw()
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
            
            total_points = 0
            all_timestamps = []
            
            for i, config in enumerate(self.signal_configs):
                # 过滤对应CAN ID的消息
                filtered_messages = [msg for msg in self.messages if msg['can_id'] == config['can_id']]
                
                if not filtered_messages:
                    continue
                
                # 提取信号数据
                timestamps = []
                values = []
                
                for msg in filtered_messages:
                    # 应用时间范围过滤
                    if time_start is not None and msg['timestamp'] < time_start:
                        continue
                    if time_end is not None and msg['timestamp'] > time_end:
                        continue
                    
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
                
                if timestamps:
                    current_ax = axes[i if subplot_mode else 0]
                    
                    # 绘制曲线
                    line = current_ax.plot(timestamps, values, 
                           color=config['color'], 
                           linewidth=1.5, 
                           marker='o', 
                           markersize=2,
                           label=f"{config['name']} (0x{config['can_id']:X})")
                    
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
            
            # 调整布局
            self.figure.tight_layout()
            
            # 更新画布
            self.canvas.draw()
            
            # 更新状态信息
            range_info = ""
            if self.current_time_range:
                range_info = f" | 时间范围: {self.current_time_range[0]:.3f}s-{self.current_time_range[1]:.3f}s"
            
            mode_info = "子图模式" if subplot_mode else "叠加模式"
            self.status_label.config(text=f"已绘制 {len(self.signal_configs)} 个信号 ({mode_info})，共 {total_points} 个数据点{range_info}")
            
        except Exception as e:
            messagebox.showerror("错误", f"更新图表失败: {e}")

def main():
    """主函数"""
    root = tk.Tk()
    app = MultiSignalChartViewer(root)
    
    # 尝试加载示例文件
    sample_file = "sample_data.asc"
    if os.path.exists(sample_file):
        try:
            reader = SimpleASCReader()
            app.messages = reader.read_file(sample_file)
            app.file_label.config(text=f"已加载: {sample_file}")
            
            # 统计CAN ID
            can_id_stats = defaultdict(int)
            for msg in app.messages:
                can_id_stats[msg['can_id']] += 1
            
            # 更新CAN ID选择框
            can_ids = [f"0x{can_id:X}" for can_id in sorted(can_id_stats.keys())]
            app.can_id_combo['values'] = can_ids
            
            if can_ids:
                app.can_id_combo.current(0)
            
            app.status_label.config(text=f"已加载示例文件: {len(app.messages)} 条消息")
            
            # 初始化时间范围
            if app.messages:
                min_time = min(msg['timestamp'] for msg in app.messages)
                max_time = max(msg['timestamp'] for msg in app.messages)
                app.time_start_var.set(f"{min_time:.3f}")
                app.time_end_var.set(f"{max_time:.3f}")
                app.current_time_range = (min_time, max_time)
        except:
            pass
    
    root.mainloop()

if __name__ == "__main__":
    main()