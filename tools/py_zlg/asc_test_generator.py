#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ASC测试文件生成器
用于生成测试用的ASC文件，方便测试分割功能
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import random
import time
from datetime import datetime

class ASCTestFileGenerator:
    def __init__(self, root):
        self.root = root
        self.setup_ui()
        
    def setup_ui(self):
        """设置界面"""
        self.root.title("🧪 ASC测试文件生成器")
        self.root.geometry("600x500")
        
        # 主框架
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 标题
        ttk.Label(main_frame, text="🧪 ASC测试文件生成器", 
                 font=('Microsoft YaHei UI', 14, 'bold')).grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # 参数设置
        params_frame = ttk.LabelFrame(main_frame, text="📊 生成参数", padding="15")
        params_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        
        # 行数设置
        ttk.Label(params_frame, text="数据行数:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.line_count = tk.IntVar(value=5000)
        ttk.Spinbox(params_frame, from_=100, to=1000000, width=15, 
                   textvariable=self.line_count).grid(row=0, column=1, sticky=tk.W)
        
        # CAN ID范围
        ttk.Label(params_frame, text="CAN ID范围:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        id_frame = ttk.Frame(params_frame)
        id_frame.grid(row=1, column=1, sticky=tk.W, pady=(10, 0))
        
        self.min_id = tk.StringVar(value="100")
        self.max_id = tk.StringVar(value="7FF")
        ttk.Entry(id_frame, textvariable=self.min_id, width=8).grid(row=0, column=0)
        ttk.Label(id_frame, text=" - ").grid(row=0, column=1)
        ttk.Entry(id_frame, textvariable=self.max_id, width=8).grid(row=0, column=2)
        
        # 时间间隔
        ttk.Label(params_frame, text="时间间隔(ms):").grid(row=2, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        self.time_interval = tk.IntVar(value=10)
        ttk.Spinbox(params_frame, from_=1, to=1000, width=15,
                   textvariable=self.time_interval).grid(row=2, column=1, sticky=tk.W, pady=(10, 0))
        
        # 输出文件
        ttk.Label(params_frame, text="输出文件:").grid(row=3, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        output_frame = ttk.Frame(params_frame)
        output_frame.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.output_file = tk.StringVar(value="test_data.asc")
        ttk.Entry(output_frame, textvariable=self.output_file, width=30).grid(row=0, column=0, sticky=(tk.W, tk.E))
        ttk.Button(output_frame, text="浏览", command=self.browse_output).grid(row=0, column=1, padx=(5, 0))
        output_frame.columnconfigure(0, weight=1)
        
        params_frame.columnconfigure(1, weight=1)
        
        # 预览区域
        preview_frame = ttk.LabelFrame(main_frame, text="👀 数据预览", padding="15")
        preview_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 15))
        
        self.preview_text = tk.Text(preview_frame, height=12, width=70, font=('Consolas', 9))
        scrollbar = ttk.Scrollbar(preview_frame, orient="vertical", command=self.preview_text.yview)
        self.preview_text.configure(yscrollcommand=scrollbar.set)
        
        self.preview_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)
        
        # 按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=(0, 10))
        
        ttk.Button(button_frame, text="👁️ 预览数据", command=self.preview_data).grid(row=0, column=0, padx=(0, 10))
        ttk.Button(button_frame, text="📝 生成文件", command=self.generate_file).grid(row=0, column=1, padx=(0, 10))
        ttk.Button(button_frame, text="🧹 清空", command=self.clear_preview).grid(row=0, column=2)
        
        # 配置权重
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # 初始预览
        self.preview_data()
    
    def browse_output(self):
        """浏览输出文件"""
        filename = filedialog.asksaveasfilename(
            title="保存ASC文件",
            defaultextension=".asc",
            filetypes=[("ASC文件", "*.asc"), ("所有文件", "*.*")]
        )
        if filename:
            self.output_file.set(filename)
    
    def generate_sample_lines(self, count=10):
        """生成示例数据行"""
        try:
            min_id = int(self.min_id.get(), 16)
            max_id = int(self.max_id.get(), 16)
        except:
            min_id = 0x100
            max_id = 0x7FF
        
        lines = []
        timestamp = 0.0
        interval = self.time_interval.get() / 1000.0
        
        # 简化的ASC文件头
        current_time = datetime.now()
        formatted_date = current_time.strftime('%a %b %d %H:%M:%S %Y')
        # 确保日期格式中的日期部分有适当的空格
        date_parts = formatted_date.split()
        if len(date_parts[2]) == 1:  # 如果日期是单数字，添加前导空格
            date_parts[2] = f" {date_parts[2]}"
        formatted_date = " ".join(date_parts)
        
        header = f"""date {formatted_date}
base hex timestamps absolute
// version 7.0.0"""
        
        # 生成数据行
        for i in range(count):
            can_id = random.randint(min_id, max_id)
            dlc = random.randint(1, 8)
            data_bytes = [f"{random.randint(0, 255):02X}" for _ in range(dlc)]
            data_str = " ".join(data_bytes)
            
            line = f"   {timestamp:8.6f} 1  {can_id:X}             Rx   d {dlc} {data_str}"
            lines.append(line)
            timestamp += interval
        
        return header, lines
    
    def preview_data(self):
        """预览数据"""
        header, sample_lines = self.generate_sample_lines(10)
        
        preview_content = f"{header}\n"
        preview_content += "\n".join(sample_lines[:10])
        preview_content += f"\n\n... (共 {self.line_count.get()} 行数据) ..."
        
        self.preview_text.delete(1.0, tk.END)
        self.preview_text.insert(tk.END, preview_content)
    
    def generate_file(self):
        """生成完整的ASC文件"""
        if not self.output_file.get():
            messagebox.showerror("错误", "请指定输出文件名")
            return
        
        try:
            count = self.line_count.get()
            if count < 1:
                messagebox.showerror("错误", "行数必须大于0")
                return
            
            # 生成数据
            header, _ = self.generate_sample_lines(1)
            
            with open(self.output_file.get(), 'w', encoding='utf-8') as f:
                f.write(header)
                f.write("\n")
                
                # 生成数据行
                try:
                    min_id = int(self.min_id.get(), 16)
                    max_id = int(self.max_id.get(), 16)
                except:
                    min_id = 0x100
                    max_id = 0x7FF
                
                timestamp = 0.0
                interval = self.time_interval.get() / 1000.0
                
                for i in range(count):
                    can_id = random.randint(min_id, max_id)
                    dlc = random.randint(1, 8)
                    data_bytes = [f"{random.randint(0, 255):02X}" for _ in range(dlc)]
                    data_str = " ".join(data_bytes)
                    
                    line = f"   {timestamp:8.6f} 1  {can_id:X}             Rx   d {dlc} {data_str}\n"
                    f.write(line)
                    timestamp += interval
                
                # 简洁的文件尾
                pass
            
            file_size = round(len(open(self.output_file.get(), 'r', encoding='utf-8').read()) / 1024, 2)
            messagebox.showinfo("成功", f"文件生成成功！\n行数: {count}\n文件大小: {file_size} KB\n保存位置: {self.output_file.get()}")
            
        except Exception as e:
            messagebox.showerror("错误", f"生成文件失败:\n{str(e)}")
    
    def clear_preview(self):
        """清空预览"""
        self.preview_text.delete(1.0, tk.END)

def main():
    root = tk.Tk()
    app = ASCTestFileGenerator(root)
    
    # 居中显示
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")
    
    root.mainloop()

if __name__ == "__main__":
    main()