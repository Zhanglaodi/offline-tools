# CAN多信号曲线查看器

## 📁 文件说明
- `multi_signal_chart_viewer.py` - 主程序（CAN多信号曲线查看器）
- `simple_asc_reader.py` - ASC文件解析器
- `sample_data.asc` - 示例数据文件
- `requirements.txt` - Python依赖包列表

## 🚀 快速开始
```bash
# 安装依赖
pip install -r requirements.txt

# 运行程序
python multi_signal_chart_viewer.py
```

## ✨ 主要功能
- 📈 多信号同时显示
- 🔍 交互式缩放和导航
- 📊 子图模式（x轴同步）
- 🔄 大端/小端字节序支持
- ⏱️ 精确时间范围控制
- 🎯 信号预设和自定义配置

## 🎯 使用步骤
1. 选择ASC文件
2. 配置信号参数（CAN ID、起始位、长度、系数等）
3. 选择字节序（大端/小端）
4. 添加多个信号
5. 查看曲线图（叠加模式或子图模式）
6. 使用工具栏进行缩放和导航

## 📊 字节序说明
- **big（大端）**: Motorola格式，CAN网络常用
- **little（小端）**: Intel格式，PC架构常用

这是一个功能完整的CAN信号分析工具！🎉