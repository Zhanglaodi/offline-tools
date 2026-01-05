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

版本 3.4 - 控制面板优化版

作者：揍你了哈
邮箱：1535852024@qq.com

🎯 专业级CAN信号分析工具


✨ v3.4 控制面板优化：
• 修复dbc解析扩展帧问题
• 优化信号列表显示

🖥️ v3.2：
• 📱 可滚动控制面板设计
• 🖱️ 鼠标滚轮面板导航
• 📐 面板宽度优化（420px）
• 🎨 响应式布局设计
• 🔧 DBC功能完整显示
• ⚙️ 控件自适应布局

✨ v3.1.0 DBC数据库功能：
• 🗃️ DBC数据库完整支持
• 🔄 双模式信号配置（手动/DBC）
• 🎯 专业汽车信号库集成
• 🔒 数据一致性智能保证
• 📊 信号参数标准化管理
• ⚙️ 智能UI状态控制

🔧 v3.0 交互增强：
• 🖱️ 鼠标滚轮X轴缩放
• 🖱️ 鼠标拖拽Y轴移动
• ✨ 十字线精确数据查看
• 📏 双点时间测量功能
• 🎨 防闪烁交互优化
• ⏰ 智能时间格式显示

🛠️ 技术栈：
• Python 3.8+ 核心引擎
• Tkinter 原生GUI框架
• Matplotlib 专业图表库
• NumPy 数值计算加速
• Statistics 统计分析
• 优化算法和缓存机制
• DBC解析引擎
"""

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