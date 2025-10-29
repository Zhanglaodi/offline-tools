#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CAN信号曲线图查看器
支持选择CAN ID和信号配置，实时显示曲线图
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
from pathlib import Path
from collections import defaultdict

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from simple_asc_reader import SimpleASCReader

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

class SignalChartViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("CAN信号曲线图查看器")
        self.root.geometry("1200x800")
        
        # 数据存储
        self.messages = []
        self.filtered_messages = []
        self.current_file = None
        
        # 默认信号配置
        self.signal_presets = {
            "第1字节 (0-7位)": {"start": 0, "length": 8, "factor": 1.0, "offset": 0.0, "signed": False},
            "前2字节转速 (0-15位)": {"start": 0, "length": 16, "factor": 0.25, "offset": 0.0, "signed": False},
            "温度信号 (16-23位)": {"start": 16, "length": 8, "factor": 1.0, "offset": -40.0, "signed": False},
            "电压信号 (0-11位)": {"start": 0, "length": 12, "factor": 0.01, "offset": 0.0, "signed": False},
            "有符号温度 (24-31位)": {"start": 24, "length": 8, "factor": 0.5, "offset": 0.0, "signed": True},
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
        
        # CAN ID选择
        id_frame = ttk.LabelFrame(control_frame, text="CAN ID选择", padding=5)
        id_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.can_id_var = tk.StringVar()
        self.can_id_combo = ttk.Combobox(id_frame, textvariable=self.can_id_var, state="readonly")
        self.can_id_combo.pack(fill=tk.X, pady=(0, 5))
        self.can_id_combo.bind('<<ComboboxSelected>>', self.on_can_id_changed)
        
        # 消息统计
        self.id_stats_label = ttk.Label(id_frame, text="选择CAN ID查看统计")
        self.id_stats_label.pack(fill=tk.X)
        
        # 信号配置
        signal_frame = ttk.LabelFrame(control_frame, text="信号配置", padding=5)
        signal_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 预设信号
        ttk.Label(signal_frame, text="预设信号:").pack(anchor=tk.W)
        self.preset_var = tk.StringVar()
        preset_combo = ttk.Combobox(signal_frame, textvariable=self.preset_var, 
                                  values=list(self.signal_presets.keys()), state="readonly")
        preset_combo.pack(fill=tk.X, pady=(0, 5))
        preset_combo.bind('<<ComboboxSelected>>', self.on_preset_changed)
        
        # 自定义配置
        ttk.Separator(signal_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)
        ttk.Label(signal_frame, text="自定义配置:").pack(anchor=tk.W)
        
        # 起始位
        start_frame = ttk.Frame(signal_frame)
        start_frame.pack(fill=tk.X, pady=2)
        ttk.Label(start_frame, text="起始位:", width=8).pack(side=tk.LEFT)
        self.start_bit_var = tk.StringVar(value="0")
        ttk.Entry(start_frame, textvariable=self.start_bit_var, width=10).pack(side=tk.RIGHT)
        
        # 长度
        length_frame = ttk.Frame(signal_frame)
        length_frame.pack(fill=tk.X, pady=2)
        ttk.Label(length_frame, text="长度(位):", width=8).pack(side=tk.LEFT)
        self.length_var = tk.StringVar(value="8")
        ttk.Entry(length_frame, textvariable=self.length_var, width=10).pack(side=tk.RIGHT)
        
        # 系数
        factor_frame = ttk.Frame(signal_frame)
        factor_frame.pack(fill=tk.X, pady=2)
        ttk.Label(factor_frame, text="系数:", width=8).pack(side=tk.LEFT)
        self.factor_var = tk.StringVar(value="1.0")
        ttk.Entry(factor_frame, textvariable=self.factor_var, width=10).pack(side=tk.RIGHT)
        
        # 偏移
        offset_frame = ttk.Frame(signal_frame)
        offset_frame.pack(fill=tk.X, pady=2)
        ttk.Label(offset_frame, text="偏移:", width=8).pack(side=tk.LEFT)
        self.offset_var = tk.StringVar(value="0.0")
        ttk.Entry(offset_frame, textvariable=self.offset_var, width=10).pack(side=tk.RIGHT)
        
        # 有符号
        self.signed_var = tk.BooleanVar()
        ttk.Checkbutton(signal_frame, text="有符号数", variable=self.signed_var).pack(anchor=tk.W, pady=2)
        
        # 更新按钮
        ttk.Button(signal_frame, text="更新曲线", command=self.update_chart).pack(fill=tk.X, pady=(10, 0))
        
        # 显示选项
        display_frame = ttk.LabelFrame(control_frame, text="显示选项", padding=5)
        display_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.show_raw_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(display_frame, text="显示原始值", variable=self.show_raw_var, 
                       command=self.update_chart).pack(anchor=tk.W)
        
        self.show_physical_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(display_frame, text="显示物理值", variable=self.show_physical_var,
                       command=self.update_chart).pack(anchor=tk.W)
        
        # 时间范围
        time_frame = ttk.LabelFrame(control_frame, text="时间范围", padding=5)
        time_frame.pack(fill=tk.X)
        
        self.time_start_var = tk.StringVar(value="0")
        self.time_end_var = tk.StringVar(value="10")
        
        start_time_frame = ttk.Frame(time_frame)
        start_time_frame.pack(fill=tk.X, pady=2)
        ttk.Label(start_time_frame, text="开始(s):", width=8).pack(side=tk.LEFT)
        ttk.Entry(start_time_frame, textvariable=self.time_start_var, width=10).pack(side=tk.RIGHT)
        
        end_time_frame = ttk.Frame(time_frame)
        end_time_frame.pack(fill=tk.X, pady=2)
        ttk.Label(end_time_frame, text="结束(s):", width=8).pack(side=tk.LEFT)
        ttk.Entry(end_time_frame, textvariable=self.time_end_var, width=10).pack(side=tk.RIGHT)
        
        ttk.Button(time_frame, text="应用时间范围", command=self.update_chart).pack(fill=tk.X, pady=(5, 0))
        
        # 右侧图表区域
        chart_frame = ttk.Frame(main_frame)
        chart_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 创建图表
        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.figure, chart_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 状态栏
        self.status_label = ttk.Label(self.root, text="请选择ASC文件开始分析", relief=tk.SUNKEN)
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
            self.current_file = file_path
            
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
            can_ids = [f"0x{can_id:X} ({count}条)" for can_id, count in sorted(can_id_stats.items())]
            self.can_id_combo['values'] = can_ids
            
            if can_ids:
                self.can_id_combo.current(0)
                self.on_can_id_changed()
            
            self.status_label.config(text=f"已加载 {len(self.messages)} 条消息，{len(can_id_stats)} 个CAN ID")
            
        except Exception as e:
            messagebox.showerror("错误", f"加载文件失败: {e}")
            self.status_label.config(text="加载文件失败")
    
    def on_can_id_changed(self, event=None):
        """CAN ID选择改变"""
        if not self.messages:
            return
        
        selected = self.can_id_var.get()
        if not selected:
            return
        
        # 提取CAN ID
        can_id_hex = selected.split(' ')[0]
        can_id = int(can_id_hex, 16)
        
        # 过滤消息
        self.filtered_messages = [msg for msg in self.messages if msg['can_id'] == can_id]
        
        # 更新统计信息
        if self.filtered_messages:
            first_time = self.filtered_messages[0]['timestamp']
            last_time = self.filtered_messages[-1]['timestamp']
            duration = last_time - first_time
            avg_interval = duration / (len(self.filtered_messages) - 1) if len(self.filtered_messages) > 1 else 0
            
            stats_text = f"消息数: {len(self.filtered_messages)}\n"
            stats_text += f"时间范围: {first_time:.3f}s - {last_time:.3f}s\n"
            stats_text += f"持续时间: {duration:.3f}s\n"
            stats_text += f"平均间隔: {avg_interval*1000:.1f}ms"
            
            self.id_stats_label.config(text=stats_text)
            
            # 更新时间范围
            self.time_start_var.set(f"{first_time:.3f}")
            self.time_end_var.set(f"{last_time:.3f}")
        
        self.update_chart()
    
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
            self.update_chart()
    
    def extract_signal_value(self, data_bytes, start_bit, length, factor=1.0, offset=0.0, signed=False):
        """提取信号值"""
        try:
            # 将字节转换为位数组
            bit_array = []
            for byte in data_bytes:
                for i in range(8):
                    bit_array.append((byte >> (7-i)) & 1)
            
            # 检查范围
            if start_bit + length > len(bit_array):
                return None, None
            
            # 提取信号位
            signal_bits = bit_array[start_bit:start_bit+length]
            
            # 转换为数值
            raw_value = 0
            for bit in signal_bits:
                raw_value = (raw_value << 1) | bit
            
            # 处理有符号数
            if signed and length < 32:
                if raw_value >= (1 << (length-1)):
                    raw_value -= (1 << length)
            
            # 应用系数和偏移
            physical_value = raw_value * factor + offset
            
            return raw_value, physical_value
        except:
            return None, None
    
    def update_chart(self):
        """更新图表"""
        if not self.filtered_messages:
            self.figure.clear()
            self.canvas.draw()
            return
        
        try:
            # 获取信号配置
            start_bit = int(self.start_bit_var.get())
            length = int(self.length_var.get())
            factor = float(self.factor_var.get())
            offset = float(self.offset_var.get())
            signed = self.signed_var.get()
            
            # 获取时间范围
            time_start = float(self.time_start_var.get())
            time_end = float(self.time_end_var.get())
            
            # 提取数据
            timestamps = []
            raw_values = []
            physical_values = []
            
            for msg in self.filtered_messages:
                if time_start <= msg['timestamp'] <= time_end:
                    raw, physical = self.extract_signal_value(
                        msg['data'], start_bit, length, factor, offset, signed
                    )
                    if raw is not None:
                        timestamps.append(msg['timestamp'])
                        raw_values.append(raw)
                        physical_values.append(physical)
            
            if not timestamps:
                self.figure.clear()
                ax = self.figure.add_subplot(111)
                ax.text(0.5, 0.5, '没有有效数据\n请检查信号配置', 
                       ha='center', va='center', transform=ax.transAxes, fontsize=14)
                self.canvas.draw()
                return
            
            # 清除图表
            self.figure.clear()
            
            # 创建子图
            show_raw = self.show_raw_var.get()
            show_physical = self.show_physical_var.get()
            
            if show_raw and show_physical:
                ax1 = self.figure.add_subplot(211)
                ax2 = self.figure.add_subplot(212)
            elif show_raw or show_physical:
                ax1 = self.figure.add_subplot(111)
                ax2 = None
            else:
                ax1 = self.figure.add_subplot(111)
                ax1.text(0.5, 0.5, '请选择要显示的数据类型', 
                        ha='center', va='center', transform=ax1.transAxes, fontsize=14)
                self.canvas.draw()
                return
            
            # 绘制原始值
            if show_raw:
                ax1.plot(timestamps, raw_values, 'b.-', linewidth=1.5, markersize=3, label='原始值')
                ax1.set_ylabel('原始值')
                ax1.grid(True, alpha=0.3)
                ax1.legend()
                
                # 添加统计信息
                if raw_values:
                    min_val = min(raw_values)
                    max_val = max(raw_values)
                    avg_val = sum(raw_values) / len(raw_values)
                    ax1.set_title(f'原始值 (最小:{min_val}, 最大:{max_val}, 平均:{avg_val:.2f})')
            
            # 绘制物理值
            if show_physical:
                target_ax = ax2 if ax2 else ax1
                target_ax.plot(timestamps, physical_values, 'r.-', linewidth=1.5, markersize=3, label='物理值')
                target_ax.set_ylabel('物理值')
                target_ax.set_xlabel('时间 (秒)')
                target_ax.grid(True, alpha=0.3)
                target_ax.legend()
                
                # 添加统计信息
                if physical_values:
                    min_val = min(physical_values)
                    max_val = max(physical_values)
                    avg_val = sum(physical_values) / len(physical_values)
                    target_ax.set_title(f'物理值 (最小:{min_val:.2f}, 最大:{max_val:.2f}, 平均:{avg_val:.2f})')
            
            # 设置整体标题
            selected_can_id = self.can_id_var.get().split(' ')[0]
            signal_info = f"位{start_bit}-{start_bit+length-1}"
            if factor != 1.0 or offset != 0.0:
                signal_info += f", 系数={factor}, 偏移={offset}"
            
            self.figure.suptitle(f'CAN ID {selected_can_id} 信号曲线 ({signal_info})', fontsize=14)
            
            # 调整布局
            self.figure.tight_layout()
            
            # 更新画布
            self.canvas.draw()
            
            # 更新状态
            self.status_label.config(text=f"已绘制 {len(timestamps)} 个数据点")
            
        except Exception as e:
            messagebox.showerror("错误", f"更新图表失败: {e}")

def main():
    """主函数"""
    root = tk.Tk()
    app = SignalChartViewer(root)
    
    # 尝试加载示例文件
    sample_file = "sample_data.asc"
    if os.path.exists(sample_file):
        try:
            reader = SimpleASCReader()
            app.messages = reader.read_file(sample_file)
            app.current_file = sample_file
            app.file_label.config(text=f"已加载: {sample_file}")
            
            # 统计CAN ID
            can_id_stats = defaultdict(int)
            for msg in app.messages:
                can_id_stats[msg['can_id']] += 1
            
            # 更新CAN ID选择框
            can_ids = [f"0x{can_id:X} ({count}条)" for can_id, count in sorted(can_id_stats.items())]
            app.can_id_combo['values'] = can_ids
            
            if can_ids:
                app.can_id_combo.current(0)
                app.on_can_id_changed()
            
            app.status_label.config(text=f"已加载示例文件: {len(app.messages)} 条消息")
        except:
            pass
    
    root.mainloop()

if __name__ == "__main__":
    main()