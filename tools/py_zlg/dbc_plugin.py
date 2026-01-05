#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DBC插件 - 为CAN信号分析器添加DBC文件支持
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Dict, List, Any, Optional
import random
from dbc_parser import DBCParser, DBCMessage, DBCSignal

class DBCPlugin:
    """DBC插件类"""
    
    def __init__(self, parent_app):
        self.parent_app = parent_app
        self.dbc_parser = DBCParser()
        self.dbc_loaded = False
        self.dbc_file_path = ""
        
    def create_dbc_ui(self, parent_frame):
        """创建DBC相关UI"""
        # DBC文件选择框
        dbc_frame = ttk.LabelFrame(parent_frame, text="信号配置模式", padding="5")
        dbc_frame.pack(fill=tk.X, pady=(0, 5))
        
        # 配置模式选择
        mode_frame = ttk.Frame(dbc_frame)
        mode_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(mode_frame, text="配置模式:", width=8).pack(side=tk.LEFT)
        self.config_mode_var = tk.StringVar(value="manual")
        
        manual_radio = ttk.Radiobutton(mode_frame, text="手动输入", variable=self.config_mode_var, 
                                     value="manual", command=self.on_mode_changed)
        manual_radio.pack(side=tk.LEFT, padx=(5, 15))
        
        dbc_radio = ttk.Radiobutton(mode_frame, text="DBC数据库", variable=self.config_mode_var, 
                                  value="dbc", command=self.on_mode_changed)
        dbc_radio.pack(side=tk.LEFT)
        
        # DBC模式的UI容器
        self.dbc_controls_frame = ttk.Frame(dbc_frame)
        self.dbc_controls_frame.pack(fill=tk.X, pady=(5, 0))
        
        # DBC文件选择
        dbc_file_frame = ttk.Frame(self.dbc_controls_frame)
        dbc_file_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(dbc_file_frame, text="DBC文件:", width=8).pack(side=tk.LEFT)
        self.dbc_file_var = tk.StringVar(value="未选择DBC文件")
        self.dbc_file_label = ttk.Label(dbc_file_frame, textvariable=self.dbc_file_var, 
                                       foreground="gray", width=35)
        self.dbc_file_label.pack(side=tk.LEFT, padx=(5, 0), fill=tk.X, expand=True)
        
        ttk.Button(dbc_file_frame, text="选择DBC", 
                  command=self.select_dbc_file).pack(side=tk.RIGHT, padx=(5, 0))
        
        # DBC信号选择
        signal_select_frame = ttk.Frame(self.dbc_controls_frame)
        signal_select_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(signal_select_frame, text="信号:", width=8).pack(side=tk.LEFT)
        self.dbc_signal_var = tk.StringVar()
        self.dbc_signal_combo = ttk.Combobox(signal_select_frame, textvariable=self.dbc_signal_var, 
                                           state="readonly", width=30)
        self.dbc_signal_combo.pack(side=tk.LEFT, padx=(5, 0), fill=tk.X, expand=True)
        self.dbc_signal_combo.bind('<<ComboboxSelected>>', self.on_dbc_signal_selected)
        
        ttk.Button(signal_select_frame, text="添加到列表", 
                  command=self.apply_dbc_signal).pack(side=tk.RIGHT, padx=(5, 0))
        
        # DBC信息显示
        info_frame = ttk.Frame(self.dbc_controls_frame)
        info_frame.pack(fill=tk.X)
        
        self.dbc_info_var = tk.StringVar(value="请选择DBC文件")
        self.dbc_info_label = ttk.Label(info_frame, textvariable=self.dbc_info_var, 
                                      foreground="blue", font=("Arial", 8))
        self.dbc_info_label.pack(side=tk.LEFT)
        
        # 模式状态提示
        status_frame = ttk.Frame(dbc_frame)
        status_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.mode_status_var = tk.StringVar(value="当前模式: 手动输入")
        self.mode_status_label = ttk.Label(status_frame, textvariable=self.mode_status_var, 
                                          foreground="darkgreen", font=("Arial", 9, "bold"))
        self.mode_status_label.pack(side=tk.LEFT)
        
        # 初始状态：隐藏DBC控件
        self.on_mode_changed()
        
        return dbc_frame
    
    def on_mode_changed(self):
        """配置模式切换处理"""
        mode = self.config_mode_var.get()
        
        if mode == "manual":
            # 隐藏DBC控件
            self.dbc_controls_frame.pack_forget()
            # 启用手动输入控件和添加按钮
            self.enable_manual_controls(True)
            self.enable_add_signal_button(True)
            # 更新状态显示
            self.mode_status_var.set("当前模式: 手动输入 ✏️")
            
        elif mode == "dbc":
            # 显示DBC控件
            self.dbc_controls_frame.pack(fill=tk.X, pady=(5, 0))
            # 禁用手动输入控件和添加按钮
            self.enable_manual_controls(False)
            self.enable_add_signal_button(False)
            # 更新状态显示
            if self.dbc_loaded:
                self.mode_status_var.set("当前模式: DBC数据库 📊")
            else:
                self.mode_status_var.set("当前模式: DBC数据库 (未加载) ⚠️")
    
    def enable_add_signal_button(self, enabled: bool):
        """启用/禁用添加信号按钮"""
        try:
            if hasattr(self.parent_app, 'add_signal_btn'):
                state = "normal" if enabled else "disabled"
                self.parent_app.add_signal_btn.config(state=state)
        except Exception as e:
            print(f"设置添加信号按钮状态失败: {e}")
    
    def enable_manual_controls(self, enabled: bool):
        """启用/禁用主界面的手动输入控件"""
        try:
            # 控制手动输入区域的状态
            state = "normal" if enabled else "disabled"
            combo_state = "readonly" if enabled else "disabled"
            
            # 直接控制主界面的输入控件
            control_entries = [
                ('start_bit_var', 'Entry'),
                ('length_var', 'Entry'),
                ('factor_var', 'Entry'), 
                ('offset_var', 'Entry'),
                ('signal_name_var', 'Entry')
            ]
            
            # 控制Entry控件
            for var_name, widget_type in control_entries:
                if hasattr(self.parent_app, var_name):
                    self._find_and_control_entry(self.parent_app.root, 
                                               getattr(self.parent_app, var_name), state)
            
            # 直接控制特定控件
            # 控制CAN ID下拉框
            if hasattr(self.parent_app, 'can_id_combo'):
                self.parent_app.can_id_combo.config(state=combo_state)
            
            # 控制字节序下拉框
            if hasattr(self.parent_app, 'endian_combo'):
                self.parent_app.endian_combo.config(state=combo_state)
            
            # 控制有符号数复选框
            if hasattr(self.parent_app, 'signed_var'):
                self._find_and_control_checkbutton(self.parent_app.root, 
                                                  self.parent_app.signed_var, state)
            
            # 更新说明文本
            if hasattr(self, 'dbc_info_var'):
                if enabled:
                    if self.dbc_loaded:
                        self.dbc_info_var.set("已切换到手动输入模式")
                    else:
                        self.dbc_info_var.set("手动输入模式 - 请手动填写信号参数")
                else:
                    if self.dbc_loaded:
                        self.dbc_info_var.set("DBC模式 - 请从数据库选择信号")
                    else:
                        self.dbc_info_var.set("DBC模式 - 请先选择DBC文件")
                    
        except Exception as e:
            print(f"设置手动控件状态失败: {e}")
    
    def _find_and_control_entry(self, widget, target_var, state):
        """查找并控制Entry控件"""
        try:
            if isinstance(widget, ttk.Entry):
                try:
                    textvariable = widget.cget('textvariable')
                    if textvariable == str(target_var):
                        widget.config(state=state)
                        return
                except (tk.TclError, AttributeError):
                    pass
            
            # 递归处理子控件
            for child in widget.winfo_children():
                self._find_and_control_entry(child, target_var, state)
                
        except Exception:
            pass
    
    def _find_and_control_checkbutton(self, widget, target_var, state):
        """查找并控制Checkbutton控件"""
        try:
            if isinstance(widget, ttk.Checkbutton):
                try:
                    variable = widget.cget('variable')
                    if variable == str(target_var):
                        widget.config(state=state)
                        return
                except (tk.TclError, AttributeError):
                    pass
            
            # 递归处理子控件
            for child in widget.winfo_children():
                self._find_and_control_checkbutton(child, target_var, state)
                
        except Exception:
            pass
    
    def select_dbc_file(self):
        """选择DBC文件"""
        file_path = filedialog.askopenfilename(
            title="选择DBC文件",
            filetypes=[("DBC files", "*.dbc"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            # 解析DBC文件
            success = self.dbc_parser.parse_file(file_path)
            
            if success:
                self.dbc_loaded = True
                self.dbc_file_path = file_path
                
                # 更新UI
                import os
                filename = os.path.basename(file_path)
                self.dbc_file_var.set(filename)
                self.dbc_file_label.config(foreground="green")
                
                # 更新信号列表
                self.update_signal_list()
                
                # 更新信息显示
                total_signals = sum(len(msg.signals) for msg in self.dbc_parser.messages)
                self.dbc_info_var.set(f"已加载: {len(self.dbc_parser.messages)}个消息, {total_signals}个信号")
                
                # 更新模式状态显示
                if self.config_mode_var.get() == "dbc":
                    self.mode_status_var.set("当前模式: DBC数据库 📊")
                
                messagebox.showinfo("成功", f"DBC文件加载成功!\n消息数: {len(self.dbc_parser.messages)}\n信号数: {total_signals}")
                
            else:
                messagebox.showerror("错误", "DBC文件解析失败")
                
        except Exception as e:
            messagebox.showerror("错误", f"加载DBC文件失败: {e}")
    
    def update_signal_list(self):
        """更新信号选择列表"""
        if not self.dbc_loaded:
            return
        
        # 构建信号列表
        signal_options = []
        for message in self.dbc_parser.messages:
            for signal in message.signals:
                # 格式: "消息名.信号名 (0x123) - 单位" 或 "消息名.信号名 (0x123 Ext) - 单位"
                can_id_str = f"0x{message.can_id:X}"
                if message.is_extended:
                    can_id_str += " Ext"
                option = f"{message.name}.{signal.name} ({can_id_str})"
                if signal.unit:
                    option += f" - {signal.unit}"
                signal_options.append(option)
        
        # 更新下拉框
        self.dbc_signal_combo['values'] = signal_options
        
        if signal_options:
            self.dbc_signal_combo.current(0)
            self.on_dbc_signal_selected(None)
    
    def on_dbc_signal_selected(self, event):
        """信号选择变化事件"""
        if not self.dbc_loaded:
            return
        
        selected = self.dbc_signal_var.get()
        if not selected:
            return
        
        # 解析选择的信号
        message, signal = self.parse_signal_selection(selected)
        if message and signal:
            # 显示信号详细信息
            info = f"起始位:{signal.start_bit} 长度:{signal.length} 系数:{signal.factor} 偏移:{signal.offset}"
            if signal.comment:
                info += f" | {signal.comment}"
            self.dbc_info_var.set(info)
    
    def parse_signal_selection(self, selection: str):
        """解析信号选择字符串"""
        try:
            # 格式: "消息名.信号名 (0x123) - 单位" 或 "消息名.信号名 (0x123 Ext) - 单位"
            parts = selection.split('(')
            if len(parts) < 2:
                return None, None
            
            # 提取消息名和信号名
            msg_signal_part = parts[0].strip()
            if '.' not in msg_signal_part:
                return None, None
            
            message_name, signal_name = msg_signal_part.rsplit('.', 1)
            
            # 提取CAN ID（可能包含 "Ext" 标记）
            can_id_part = parts[1].split(')')[0].strip()
            # 移除 "Ext" 标记（如果存在）
            can_id_hex = can_id_part.split()[0]  # 取第一部分，例如 "0x123" 或 "0x123 Ext" 中的 "0x123"
            can_id = int(can_id_hex, 16)
            
            # 查找对应的消息和信号
            for message in self.dbc_parser.messages:
                if message.name == message_name and message.can_id == can_id:
                    for signal in message.signals:
                        if signal.name == signal_name:
                            return message, signal
            
            return None, None
            
        except Exception as e:
            print(f"解析信号选择失败: {e}")
            return None, None
    
    def apply_dbc_signal(self):
        """应用选中的DBC信号到主界面"""
        if not self.dbc_loaded:
            messagebox.showwarning("警告", "请先加载DBC文件")
            return
        
        selected = self.dbc_signal_var.get()
        if not selected:
            messagebox.showwarning("警告", "请选择一个信号")
            return
        
        # 解析选择的信号
        message, signal = self.parse_signal_selection(selected)
        if not message or not signal:
            messagebox.showerror("错误", "无法解析选中的信号")
            return
        
        try:
            # 检查信号名称唯一性
            signal_display_name = f"{message.name}.{signal.name}"
            if signal.unit:
                signal_display_name += f" ({signal.unit})"
            
            # 检查是否已存在相同名称的信号
            existing_signals = [config['name'] for config in self.parent_app.signal_configs]
            if signal_display_name in existing_signals:
                result = messagebox.askyesno("信号已存在", 
                    f"信号 '{signal_display_name}' 已存在。\n是否要替换现有信号？")
                if not result:
                    return
                # 删除现有信号
                self.remove_existing_signal(signal_display_name)
            
            # 直接添加信号到列表中
            self.add_dbc_signal_to_list(message, signal, signal_display_name)
            
            messagebox.showinfo("成功", f"信号 '{signal_display_name}' 已添加到信号列表")
            
        except Exception as e:
            messagebox.showerror("错误", f"应用信号失败: {e}")
    
    def remove_existing_signal(self, signal_name: str):
        """删除已存在的信号"""
        try:
            # 从信号配置列表中删除
            self.parent_app.signal_configs = [
                config for config in self.parent_app.signal_configs 
                if config['name'] != signal_name
            ]
            
            # 从界面列表中删除
            for i in range(self.parent_app.signal_listbox.size()):
                if signal_name in self.parent_app.signal_listbox.get(i):
                    self.parent_app.signal_listbox.delete(i)
                    break
                    
        except Exception as e:
            print(f"删除现有信号失败: {e}")
    
    def add_dbc_signal_to_list(self, message, signal, signal_display_name):
        """将DBC信号直接添加到信号列表"""
        try:
            # 检查是否已加载ASC文件
            if not self.parent_app.messages:
                messagebox.showwarning("警告", "请先加载ASC文件")
                return
            
            # 检查CAN ID是否存在于ASC文件中
            can_id = message.can_id
            test_messages = [msg for msg in self.parent_app.messages if msg['can_id'] == can_id]
            if not test_messages:
                messagebox.showwarning("警告", 
                    f"当前ASC文件中未找到CAN ID 0x{can_id:X}\n请确保已加载包含该消息的ASC文件")
                return
            
            # 创建信号配置（格式必须与主程序add_signal一致）
            signal_config = {
                'name': signal_display_name,
                'can_id': can_id,  # 使用整数格式，不是字符串
                'start_bit': signal.start_bit,
                'length': signal.length,
                'factor': signal.factor,
                'offset': signal.offset,
                'signed': signal.value_type == 'signed',
                'endian': 'little' if signal.byte_order == 'little_endian' else 'big',
                'color': self.parent_app.colors[len(self.parent_app.signal_configs) % len(self.parent_app.colors)]
            }
            
            # 添加到信号配置列表
            self.parent_app.signal_configs.append(signal_config)
            
            # 计算帧统计信息（与主程序保持一致）
            frame_stats = self.parent_app.calculate_frame_stats(can_id)
            
            # 更新界面显示（格式与主程序保持一致）
            can_id_str = f"0x{can_id:X}"
            endian_text = "大端" if signal_config['endian'] == "big" else "小端"
            start_bit = signal.start_bit
            length = signal.length
            
            # 格式化位置信息
            if signal_config['endian'] == "big":
                position_text = f"起始位:{start_bit}(MSB) | 长度:{length}位"
            else:
                position_text = f"起始位:{start_bit}(LSB) | 长度:{length}位"
            
            if frame_stats:
                period_text = f"{frame_stats['period_ms']:.1f}ms"
                drop_text = f"{frame_stats['dropped_frames']}帧({frame_stats['drop_rate']:.1f}%)"
                display_text = f"{signal_display_name} | {can_id_str} | {position_text} | {endian_text} | 周期:{period_text} | 丢帧:{drop_text}"
            else:
                display_text = f"{signal_display_name} | {can_id_str} | {position_text} | {endian_text} | 统计:计算失败"
            
            self.parent_app.signal_listbox.insert(tk.END, display_text)
            
            # 更新状态
            if hasattr(self.parent_app, 'status_label'):
                self.parent_app.status_label.config(text=f"已添加DBC信号: {signal_display_name}")
            
            # 自动更新图表
            self.parent_app.update_chart()
            
        except Exception as e:
            print(f"添加DBC信号到列表失败: {e}")
            raise
    
    def get_next_color(self):
        """获取下一个可用颜色"""
        if hasattr(self.parent_app, 'colors'):
            used_colors = [config.get('color') for config in self.parent_app.signal_configs]
            available_colors = [c for c in self.parent_app.colors if c not in used_colors]
            if available_colors:
                return available_colors[0]
            else:
                # 如果所有颜色都用完了，返回随机颜色
                import random
                return random.choice(self.parent_app.colors)
        return 'blue'
    
    def apply_to_main_interface(self, message: DBCMessage, signal: DBCSignal):
        """将DBC信号参数应用到主界面"""
        # 设置CAN ID
        can_id_text = f"0x{message.can_id:X}"
        
        # 检查CAN ID是否在列表中
        can_id_values = list(self.parent_app.can_id_combo['values'])
        matching_ids = [v for v in can_id_values if can_id_text in v]
        
        if matching_ids:
            # 找到匹配的CAN ID，设置为当前选择
            self.parent_app.can_id_var.set(matching_ids[0])
        else:
            # 如果没有找到，提示用户先加载包含该CAN ID的ASC文件
            messagebox.showwarning("警告", 
                f"当前ASC文件中未找到CAN ID {can_id_text}\n请确保已加载包含该消息的ASC文件")
            return
        
        # 临时启用手动控件以便填入DBC数据
        self.enable_manual_controls(True)
        
        # 设置信号参数
        self.parent_app.start_bit_var.set(str(signal.start_bit))
        self.parent_app.length_var.set(str(signal.length))
        self.parent_app.factor_var.set(str(signal.factor))
        self.parent_app.offset_var.set(str(signal.offset))
        
        # 设置字节序
        if signal.byte_order == 'little_endian':
            self.parent_app.endian_var.set("little")
        else:
            self.parent_app.endian_var.set("big")
        
        # 设置有符号/无符号
        self.parent_app.signed_var.set(signal.value_type == 'signed')
        
        # 设置信号名
        signal_display_name = f"{message.name}.{signal.name}"
        if signal.unit:
            signal_display_name += f" ({signal.unit})"
        
        self.parent_app.signal_name_var.set(signal_display_name)
        
        # 如果当前是DBC模式，恢复控件状态
        if self.config_mode_var.get() == "dbc":
            self.enable_manual_controls(False)
    
    def get_dbc_info(self) -> Dict[str, Any]:
        """获取DBC信息"""
        if not self.dbc_loaded:
            return {}
        
        return {
            'loaded': True,
            'file_path': self.dbc_file_path,
            'messages_count': len(self.dbc_parser.messages),
            'signals_count': sum(len(msg.signals) for msg in self.dbc_parser.messages),
            'nodes_count': len(self.dbc_parser.nodes)
        }
    
    def export_dbc_signals(self) -> List[Dict[str, Any]]:
        """导出DBC信号列表"""
        if not self.dbc_loaded:
            return []
        
        return self.dbc_parser.export_signal_list()
    
    def search_dbc_signals(self, keyword: str) -> List[tuple]:
        """搜索DBC信号"""
        if not self.dbc_loaded:
            return []
        
        return self.dbc_parser.search_signals_by_name(keyword)

# 在主程序中集成DBC插件的函数
def integrate_dbc_plugin(main_app):
    """在主程序中集成DBC插件"""
    # 创建DBC插件实例
    dbc_plugin = DBCPlugin(main_app)
    
    # 在主界面中添加DBC UI
    # 这需要在主程序的UI创建部分调用
    # dbc_frame = dbc_plugin.create_dbc_ui(main_app.some_parent_frame)
    
    # 将插件实例存储在主程序中
    main_app.dbc_plugin = dbc_plugin
    
    return dbc_plugin