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

版本 3.0.0 - 交互式增强版

作者：揍你了哈
邮箱：1535852024@qq.com

🎯 专业级CAN信号分析工具

✨ 最新特性（v3.0）：
• 🖱️ 鼠标滚轮X轴缩放
• 🖱️ 鼠标拖拽Y轴移动
• ✨ 十字线精确数据查看
• 📏 双点时间测量功能
• 🎨 防闪烁交互优化
• ⏰ 智能时间格式显示

🔧 核心功能：
• 多信号同时分析
• 智能丢帧检测
• 子图同步显示
• 字节序完全支持
• 高性能算法
• 专业级交互体验

📊 分析能力：
• 信号周期自动计算
• 丢帧率精确统计
• 通信质量评估
• 时间间隔测量
• 数据点精确查看
• 多维度对比分析

🛠️ 技术栈：
• Python 3.8+ 核心引擎
• Tkinter 原生GUI框架
• Matplotlib 专业图表库
• NumPy 数值计算加速
• Statistics 统计分析
• 优化算法和缓存机制

📧 技术支持：
算法大师倾力打造，性能优化专家精心调优
交互体验设计师匠心雕琢，专业工程师持续维护"""

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