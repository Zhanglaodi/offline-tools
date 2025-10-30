# -*- coding: utf-8 -*-
"""
帮助文本管理器
管理所有帮助相关的文本内容
"""

import os

class HelpTextManager:
    """帮助文本管理器"""
    
    def __init__(self, help_dir=None):
        if help_dir is None:
            self.help_dir = os.path.join(os.path.dirname(__file__), 'help_texts')
        else:
            self.help_dir = help_dir
    
    def load_text(self, filename):
        """加载文本文件"""
        try:
            file_path = os.path.join(self.help_dir, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return f"帮助文件 {filename} 不存在"
        except Exception as e:
            return f"加载帮助文件 {filename} 时出错: {str(e)}"
    
    def get_user_guide(self):
        """获取用户指南"""
        return self.load_text('user_guide.txt')
    
    def get_shortcuts(self):
        """获取快捷键说明"""
        return self.load_text('shortcuts.txt')
    
    def get_features_basic(self):
        """获取基础功能说明"""
        return self.load_text('features_basic.txt')
    
    def get_features_advanced(self):
        """获取高级功能说明"""
        return self.load_text('features_advanced.txt')
    
    def get_features_technical(self):
        """获取技术特性说明"""
        return self.load_text('features_technical.txt')
    
    def get_about_info(self):
        """获取关于信息（硬编码）"""
        return """CAN多信号曲线图查看器

版本 2.0.0

作者：zxt
邮箱：1535852024@qq.com

🎯 专业级CAN信号分析工具

✨ 主要特性：
• 多信号同时分析
• 智能丢帧检测
• 子图同步显示
• 字节序支持
• 高性能算法
• 交互式图表

🛠️ 技术栈：
• Python 3.8+
• Tkinter GUI
• Matplotlib 图表
• NumPy 数值计算
• Statistics 统计分析

📧 技术支持：
算法大师倾力打造，性能优化专家精心调优"""

    def list_available_files(self):
        """列出所有可用的帮助文件"""
        try:
            return [f for f in os.listdir(self.help_dir) if f.endswith('.txt')]
        except Exception:
            return []

if __name__ == "__main__":
    # 测试帮助文本管理器
    manager = HelpTextManager()
    print("可用的帮助文件:")
    for file in manager.list_available_files():
        print(f"  - {file}")
    
    print("\n用户指南预览:")
    guide = manager.get_user_guide()
    print(guide[:200] + "..." if len(guide) > 200 else guide)