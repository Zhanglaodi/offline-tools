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
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
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
        
        # 右侧图表区域
        chart_frame = ttk.Frame(main_frame)
        chart_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 创建图表
        self.figure = Figure(figsize=(10, 8), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.figure, chart_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
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
                'color': self.colors[len(self.signal_configs) % len(self.colors)]
            }
            
            self.signal_configs.append(signal_config)
            
            # 更新列表显示
            display_text = f"{name} | {can_id_str} | {start_bit}-{start_bit+length-1}位"
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
        if not self.signal_configs:
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, '请添加信号来显示曲线图', 
                   ha='center', va='center', transform=ax.transAxes, fontsize=16)
            self.canvas.draw()
            return
        
        try:
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            
            total_points = 0
            
            for i, config in enumerate(self.signal_configs):
                # 过滤对应CAN ID的消息
                filtered_messages = [msg for msg in self.messages if msg['can_id'] == config['can_id']]
                
                if not filtered_messages:
                    continue
                
                # 提取信号数据
                timestamps = []
                values = []
                
                for msg in filtered_messages:
                    raw, physical = self.extract_signal_value(
                        msg['data'], 
                        config['start_bit'], 
                        config['length'], 
                        config['factor'], 
                        config['offset'], 
                        config['signed']
                    )
                    if physical is not None:
                        timestamps.append(msg['timestamp'])
                        values.append(physical)
                
                if timestamps:
                    # 绘制曲线
                    ax.plot(timestamps, values, 
                           color=config['color'], 
                           linewidth=1.5, 
                           marker='o', 
                           markersize=2,
                           label=f"{config['name']} (0x{config['can_id']:X})")
                    total_points += len(timestamps)
            
            # 设置图表属性
            ax.set_xlabel('时间 (秒)')
            ax.set_ylabel('信号值')
            ax.set_title('CAN多信号曲线图')
            
            if self.show_grid_var.get():
                ax.grid(True, alpha=0.3)
            
            if self.show_legend_var.get() and self.signal_configs:
                ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            
            # 调整布局
            self.figure.tight_layout()
            
            # 更新画布
            self.canvas.draw()
            
            self.status_label.config(text=f"已绘制 {len(self.signal_configs)} 个信号，共 {total_points} 个数据点")
            
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
        except:
            pass
    
    root.mainloop()

if __name__ == "__main__":
    main()