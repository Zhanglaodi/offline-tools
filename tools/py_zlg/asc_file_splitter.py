#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ASC文件分割器 - 现代化UI版本
功能：将大型ASC文件按指定数量分割成多个小文件
作者：AI编程助手
日期：2025-10-30
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import math
from pathlib import Path
import threading
import time

class ASCFileSplitterGUI:
    def __init__(self, root):
        self.root = root
        self.setup_ui()
        self.input_file = ""
        self.output_dir = ""
        self.is_processing = False
        
        # 缓存文件分析结果，避免重复读取
        self.cached_file_info = {
            'file_path': '',
            'total_lines': 0,
            'data_lines': 0,
            'file_size': 0
        }
        self.update_timer = None  # 防抖定时器
        
    def setup_ui(self):
        """设置现代化用户界面"""
        self.root.title("🔪 ASC文件分割器 v1.0")
        self.root.geometry("800x650")
        self.root.minsize(600, 500)
        
        # 设置主题色
        style = ttk.Style()
        style.theme_use('clam')
        
        # 配置颜色方案
        style.configure('Title.TLabel', font=('Microsoft YaHei UI', 16, 'bold'), foreground='#2c3e50')
        style.configure('Subtitle.TLabel', font=('Microsoft YaHei UI', 10), foreground='#34495e')
        style.configure('Info.TLabel', font=('Microsoft YaHei UI', 9), foreground='#7f8c8d')
        style.configure('Success.TLabel', font=('Microsoft YaHei UI', 9), foreground='#27ae60')
        style.configure('Error.TLabel', font=('Microsoft YaHei UI', 9), foreground='#e74c3c')
        
        # 主容器
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 标题区域
        title_frame = ttk.Frame(main_frame)
        title_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20))
        
        ttk.Label(title_frame, text="🔪 ASC文件分割器", style='Title.TLabel').grid(row=0, column=0, sticky=tk.W)
        ttk.Label(title_frame, text="将大型ASC文件智能分割成多个小文件", style='Subtitle.TLabel').grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        
        # 文件选择区域
        file_frame = ttk.LabelFrame(main_frame, text="📁 文件选择", padding="15")
        file_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        
        # 输入文件选择
        ttk.Label(file_frame, text="输入ASC文件：", style='Info.TLabel').grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        input_frame = ttk.Frame(file_frame)
        input_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.input_file_var = tk.StringVar()
        self.input_entry = ttk.Entry(input_frame, textvariable=self.input_file_var, width=60, state='readonly')
        self.input_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        
        ttk.Button(input_frame, text="📂 浏览", command=self.browse_input_file).grid(row=0, column=1)
        input_frame.columnconfigure(0, weight=1)
        
        # 输出目录选择
        ttk.Label(file_frame, text="输出目录：", style='Info.TLabel').grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        output_frame = ttk.Frame(file_frame)
        output_frame.grid(row=3, column=0, sticky=(tk.W, tk.E))
        
        self.output_dir_var = tk.StringVar()
        self.output_entry = ttk.Entry(output_frame, textvariable=self.output_dir_var, width=60, state='readonly')
        self.output_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        
        ttk.Button(output_frame, text="📁 选择", command=self.browse_output_dir).grid(row=0, column=1)
        output_frame.columnconfigure(0, weight=1)
        file_frame.columnconfigure(0, weight=1)
        
        # 分割设置区域
        settings_frame = ttk.LabelFrame(main_frame, text="⚙️ 分割设置", padding="15")
        settings_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        
        # 分割方式选择
        split_method_frame = ttk.Frame(settings_frame)
        split_method_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        
        ttk.Label(split_method_frame, text="分割方式：", style='Info.TLabel').grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        
        self.split_method = tk.StringVar(value="count")
        ttk.Radiobutton(split_method_frame, text="按文件数量", variable=self.split_method, 
                       value="count", command=self.on_method_change).grid(row=0, column=1, padx=(0, 20))
        ttk.Radiobutton(split_method_frame, text="按行数", variable=self.split_method, 
                       value="lines", command=self.on_method_change).grid(row=0, column=2)
        
        # 数值输入区域
        value_frame = ttk.Frame(settings_frame)
        value_frame.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        self.value_label = ttk.Label(value_frame, text="分割文件数量：", style='Info.TLabel')
        self.value_label.grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        
        # 数值输入框和调节器
        input_frame = ttk.Frame(value_frame)
        input_frame.grid(row=0, column=1, sticky=tk.W)
        
        self.split_value = tk.IntVar(value=2)
        self.value_spinbox = ttk.Spinbox(input_frame, from_=2, to=1000, width=10, 
                                        textvariable=self.split_value, command=self.update_preview)
        self.value_spinbox.grid(row=0, column=0, padx=(0, 10))
        
        # 文件预览信息
        self.info_label = ttk.Label(settings_frame, text="", style='Info.TLabel')
        self.info_label.grid(row=2, column=0, sticky=tk.W, pady=(10, 0))
        
        settings_frame.columnconfigure(0, weight=1)
        
        # 进度区域
        progress_frame = ttk.LabelFrame(main_frame, text="📊 处理进度", padding="15")
        progress_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100, length=400)
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.status_label = ttk.Label(progress_frame, text="准备就绪", style='Info.TLabel')
        self.status_label.grid(row=1, column=0, sticky=tk.W)
        
        progress_frame.columnconfigure(0, weight=1)
        
        # 操作按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=(0, 10))
        
        self.start_button = ttk.Button(button_frame, text="🚀 开始分割", command=self.start_split, style='Accent.TButton')
        self.start_button.grid(row=0, column=0, padx=(0, 10))
        
        ttk.Button(button_frame, text="📋 查看结果", command=self.view_results).grid(row=0, column=1, padx=(0, 10))
        ttk.Button(button_frame, text="❌ 清空", command=self.clear_all).grid(row=0, column=2, padx=(0, 10))
        ttk.Button(button_frame, text="❓ 帮助", command=self.show_help).grid(row=0, column=3)
        
        # 配置权重
        main_frame.columnconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # 绑定事件
        self.split_value.trace('w', self.update_preview)
        
    def browse_input_file(self):
        """浏览输入文件"""
        filename = filedialog.askopenfilename(
            title="选择ASC文件",
            filetypes=[("ASC文件", "*.asc"), ("所有文件", "*.*")]
        )
        if filename:
            self.input_file = filename
            self.input_file_var.set(filename)
            # 自动设置输出目录为输入文件所在目录
            if not self.output_dir:
                self.output_dir = os.path.dirname(filename)
                self.output_dir_var.set(self.output_dir)
            
            # 清除缓存，强制重新分析文件
            self.cached_file_info['file_path'] = ''
            self.analyze_file_in_background()
    
    def browse_output_dir(self):
        """浏览输出目录"""
        directory = filedialog.askdirectory(title="选择输出目录")
        if directory:
            self.output_dir = directory
            self.output_dir_var.set(directory)
    
    def on_method_change(self):
        """分割方式改变时的处理"""
        if self.split_method.get() == "count":
            self.value_label.config(text="分割文件数量：")
            self.value_spinbox.config(from_=2, to=1000)
            self.split_value.set(2)
        else:
            self.value_label.config(text="每个文件行数：")
            self.value_spinbox.config(from_=100, to=1000000)
            self.split_value.set(1000)
        self.update_preview_debounced()
    
    def analyze_file_in_background(self):
        """在后台分析文件，避免阻塞UI"""
        if not self.input_file or not os.path.exists(self.input_file):
            self.info_label.config(text="")
            return
        
        # 如果文件已经分析过，直接更新预览
        if self.cached_file_info['file_path'] == self.input_file:
            self.update_preview_from_cache()
            return
        
        # 显示分析中状态
        self.info_label.config(text="正在分析文件...")
        
        def analyze_worker():
            try:
                # 读取并分析文件
                with open(self.input_file, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                
                # 解析文件结构，获取数据行数
                _, data_lines, _ = self.parse_asc_file(lines)
                data_line_count = len(data_lines)
                total_line_count = len(lines)
                file_size = os.path.getsize(self.input_file) / (1024 * 1024)  # MB
                
                # 更新缓存
                self.cached_file_info = {
                    'file_path': self.input_file,
                    'total_lines': total_line_count,
                    'data_lines': data_line_count,
                    'file_size': file_size
                }
                
                # 在主线程中更新UI
                self.root.after(0, self.update_preview_from_cache)
                
            except Exception as e:
                self.root.after(0, lambda: self.info_label.config(text=f"读取文件信息失败: {str(e)}"))
        
        # 在后台线程中执行文件分析
        thread = threading.Thread(target=analyze_worker)
        thread.daemon = True
        thread.start()
    
    def update_preview_debounced(self, *args):
        """防抖的预览更新，避免频繁触发"""
        # 取消之前的定时器
        if self.update_timer:
            self.root.after_cancel(self.update_timer)
        
        # 设置新的定时器，300ms后执行更新
        self.update_timer = self.root.after(300, self.update_preview_from_cache)
    
    def update_preview_from_cache(self):
        """从缓存中更新预览信息，避免重复读取文件"""
        if not self.input_file or self.cached_file_info['file_path'] != self.input_file:
            self.info_label.config(text="")
            return
        
        try:
            data_line_count = self.cached_file_info['data_lines']
            total_line_count = self.cached_file_info['total_lines']
            file_size = self.cached_file_info['file_size']
            
            if self.split_method.get() == "count":
                file_count = self.split_value.get()
                if file_count > 0:
                    lines_per_file = math.ceil(data_line_count / file_count)
                    info_text = f"总行数: {total_line_count:,} | 数据行数: {data_line_count:,} | 文件大小: {file_size:.1f}MB | 将分割为 {file_count} 个文件，每个约 {lines_per_file:,} 行数据"
                else:
                    info_text = f"总行数: {total_line_count:,} | 数据行数: {data_line_count:,} | 文件大小: {file_size:.1f}MB"
            else:
                lines_per_file = self.split_value.get()
                if lines_per_file > 0:
                    file_count = math.ceil(data_line_count / lines_per_file)
                    info_text = f"总行数: {total_line_count:,} | 数据行数: {data_line_count:,} | 文件大小: {file_size:.1f}MB | 将分割为 {file_count} 个文件，每个 {lines_per_file:,} 行数据"
                else:
                    info_text = f"总行数: {total_line_count:,} | 数据行数: {data_line_count:,} | 文件大小: {file_size:.1f}MB"
            
            self.info_label.config(text=info_text)
            
        except Exception as e:
            self.info_label.config(text=f"更新预览失败: {str(e)}")

    def update_preview(self, *args):
        """更新预览信息（保持兼容性，内部调用防抖版本）"""
        self.update_preview_debounced(*args)
    
    def validate_inputs(self):
        """验证输入"""
        if not self.input_file:
            messagebox.showerror("错误", "请选择要分割的ASC文件")
            return False
        
        if not os.path.exists(self.input_file):
            messagebox.showerror("错误", "输入文件不存在")
            return False
        
        if not self.output_dir:
            messagebox.showerror("错误", "请选择输出目录")
            return False
        
        if not os.path.exists(self.output_dir):
            messagebox.showerror("错误", "输出目录不存在")
            return False
        
        if self.split_value.get() < 2:
            messagebox.showerror("错误", "分割数量必须大于等于2")
            return False
        
        return True
    
    def start_split(self):
        """开始分割处理"""
        if not self.validate_inputs():
            return
        
        if self.is_processing:
            messagebox.showwarning("警告", "正在处理中，请稍候...")
            return
        
        # 在线程中执行分割
        self.is_processing = True
        self.start_button.config(state='disabled', text='🔄 处理中...')
        
        thread = threading.Thread(target=self.split_file_thread)
        thread.daemon = True
        thread.start()
    
    def parse_asc_file(self, lines):
        """解析ASC文件，分离文件头和数据部分"""
        header_lines = []
        data_lines = []
        footer_lines = []
        
        in_data_section = False
        
        for line in lines:
            line_stripped = line.strip().lower()
            
            # 检测数据部分开始 - 更精确的检测
            if not in_data_section:
                # 标准ASC文件头关键字
                if (line_stripped.startswith('date ') or 
                    line_stripped.startswith('base ') or
                    line_stripped.startswith('// version')):
                    header_lines.append(line)
                    continue
                # 如果遇到时间戳数据行，开始数据部分
                elif (line.strip() and len(line.strip()) > 0 and 
                      (line.strip()[0].isdigit() or line.strip().startswith('   '))):
                    # 检查是否是真正的数据行（包含时间戳）
                    parts = line.split()
                    if len(parts) >= 3 and self.is_timestamp(parts[0]):
                        in_data_section = True
                        data_lines.append(line)
                    else:
                        header_lines.append(line)
                else:
                    header_lines.append(line)
                continue
            
            # 数据部分：过滤掉注释行、空行和结束标记
            if in_data_section:
                if (line.strip() and 
                    not line.strip().startswith('//') and 
                    not line.strip().startswith('*') and
                    'end triggerblock' not in line_stripped and
                    'end of measurement' not in line_stripped):
                    data_lines.append(line)
                elif ('end triggerblock' in line_stripped or 
                      'end of measurement' in line_stripped or
                      line.strip().startswith('//')):
                    # 将结束标记和后续注释归为footer（但不写入输出文件）
                    footer_lines.append(line)
        
        return header_lines, data_lines, footer_lines
    
    def is_timestamp(self, text):
        """检查是否是时间戳格式"""
        try:
            float(text)
            return True
        except ValueError:
            return False
    
    def generate_asc_header(self, part_number, total_parts):
        """生成标准ASC文件头"""
        from datetime import datetime
        
        current_time = datetime.now()
        # 格式化日期为标准ASC格式: date Sun Oct  5 06:00:00 2025
        formatted_date = current_time.strftime('%a %b %d %H:%M:%S %Y')
        # 确保日期格式中的日期部分有适当的空格
        date_parts = formatted_date.split()
        if len(date_parts[2]) == 1:  # 如果日期是单数字，添加前导空格
            date_parts[2] = f" {date_parts[2]}"
        formatted_date = " ".join(date_parts)
        
        header = f"""date {formatted_date}
base hex timestamps absolute
// version 7.0.0
"""
        return header
    
    def generate_asc_footer(self):
        """生成ASC文件尾"""
        return ""

    def split_file_thread(self):
        """分割文件的线程函数"""
        try:
            self.root.after(0, lambda: self.status_label.config(text="正在读取文件..."))
            
            # 读取文件
            with open(self.input_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            # 解析ASC文件结构
            self.root.after(0, lambda: self.status_label.config(text="正在分析文件结构..."))
            header_lines, data_lines, footer_lines = self.parse_asc_file(lines)
            
            # 只对数据行进行分割计算
            total_data_lines = len(data_lines)
            
            if total_data_lines == 0:
                raise Exception("未找到有效的数据行")
            
            if self.split_method.get() == "count":
                file_count = self.split_value.get()
                lines_per_file = math.ceil(total_data_lines / file_count)
            else:
                lines_per_file = self.split_value.get()
                file_count = math.ceil(total_data_lines / lines_per_file)
            
            # 获取原文件名（不含扩展名）
            base_name = Path(self.input_file).stem
            
            # 分割文件
            for i in range(file_count):
                start_idx = i * lines_per_file
                end_idx = min((i + 1) * lines_per_file, total_data_lines)
                
                if start_idx >= total_data_lines:
                    break
                
                # 生成输出文件名
                output_filename = f"{base_name}_part_{i+1:03d}.asc"
                output_path = os.path.join(self.output_dir, output_filename)
                
                # 写入分割文件
                with open(output_path, 'w', encoding='utf-8') as f:
                    # 写入文件头
                    header = self.generate_asc_header(i+1, file_count)
                    f.write(header)
                    
                    # 写入数据部分
                    f.writelines(data_lines[start_idx:end_idx])
                    
                    # 写入文件尾
                    footer = self.generate_asc_footer()
                    f.write(footer)
                
                # 更新进度
                progress = ((i + 1) / file_count) * 100
                self.root.after(0, lambda p=progress: self.progress_var.set(p))
                self.root.after(0, lambda i=i, fc=file_count: self.status_label.config(
                    text=f"正在生成第 {i+1}/{fc} 个文件..."))
                
                time.sleep(0.01)  # 避免界面卡顿
            
            # 完成
            self.root.after(0, self.split_complete)
            
        except Exception as e:
            self.root.after(0, lambda: self.split_error(str(e)))
    
    def split_complete(self):
        """分割完成处理"""
        self.is_processing = False
        self.start_button.config(state='normal', text='🚀 开始分割')
        self.status_label.config(text="✅ 分割完成！", style='Success.TLabel')
        self.progress_var.set(100)
        
        messagebox.showinfo("成功", f"文件分割完成！\n输出目录: {self.output_dir}")
    
    def split_error(self, error_msg):
        """分割出错处理"""
        self.is_processing = False
        self.start_button.config(state='normal', text='🚀 开始分割')
        self.status_label.config(text=f"❌ 处理失败: {error_msg}", style='Error.TLabel')
        self.progress_var.set(0)
        
        messagebox.showerror("错误", f"分割失败:\n{error_msg}")
    
    def view_results(self):
        """查看结果目录"""
        if self.output_dir and os.path.exists(self.output_dir):
            os.startfile(self.output_dir)
        else:
            messagebox.showwarning("警告", "输出目录不存在")
    
    def clear_all(self):
        """清空所有输入"""
        self.input_file = ""
        self.output_dir = ""
        self.input_file_var.set("")
        self.output_dir_var.set("")
        self.split_value.set(2)
        self.progress_var.set(0)
        self.status_label.config(text="准备就绪", style='Info.TLabel')
        self.info_label.config(text="")
    
    def show_help(self):
        """显示帮助信息"""
        help_text = """🔪 ASC文件分割器 使用说明

📁 基本操作：
1. 点击"📂 浏览"选择要分割的ASC文件
2. 选择输出目录（默认为输入文件所在目录）
3. 选择分割方式和设置参数
4. 点击"🚀 开始分割"开始处理

⚙️ 分割方式：
• 按文件数量：指定要分割成几个文件
• 按行数：指定每个文件包含多少行

📊 输出格式：
分割后的文件命名格式：原文件名_part_001.asc

💡 小贴士：
• 支持大文件分割，处理过程中会显示进度
• 分割后的文件保持原始编码格式
• 建议在分割前备份原文件

🔗 技术支持：
如有问题请联系开发者
开发者：zhanglaodi
"""
        
        help_window = tk.Toplevel(self.root)
        help_window.title("帮助信息")
        help_window.geometry("500x400")
        help_window.resizable(False, False)
        
        text_widget = tk.Text(help_window, wrap=tk.WORD, padx=20, pady=20, font=('Microsoft YaHei UI', 10))
        text_widget.pack(fill=tk.BOTH, expand=True)
        text_widget.insert(tk.END, help_text)
        text_widget.config(state=tk.DISABLED)

def main():
    """主函数"""
    root = tk.Tk()
    app = ASCFileSplitterGUI(root)
    
    # 设置窗口图标（如果有的话）
    try:
        root.iconbitmap(default='icon.ico')
    except:
        pass
    
    # 居中显示窗口
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")
    
    root.mainloop()

if __name__ == "__main__":
    main()