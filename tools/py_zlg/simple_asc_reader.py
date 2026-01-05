#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简单的ASC文件读取器
适用于不同格式的ASC文件
"""

import re
import os
from pathlib import Path
from typing import List, Dict, Any

class SimpleASCReader:
    """简单的ASC文件读取器"""
    
    def __init__(self):
        self.messages = []
        self.file_info = {}
    
    def read_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        读取ASC文件
        
        Args:
            file_path: ASC文件路径
            
        Returns:
            消息列表
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        print(f"📁 读取文件: {file_path}")
        
        # 检测编码
        encoding = self._detect_encoding(file_path)
        print(f"🔤 检测编码: {encoding}")
        
        # 读取文件
        with open(file_path, 'r', encoding=encoding) as f:
            lines = f.readlines()
        
        print(f"📊 文件行数: {len(lines)}")
        
        # 解析文件
        self.messages = []
        self.file_info = {}
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            
            # 解析文件头信息
            if line.startswith('date'):
                self.file_info['date'] = line
            elif line.startswith('base'):
                self.file_info['base'] = line
            elif line.startswith('// version'):
                self.file_info['version'] = line
            
            # 解析CAN消息
            message = self._parse_can_message(line, line_num)
            if message:
                self.messages.append(message)
        
        print(f"✅ 解析完成: {len(self.messages)} 条CAN消息")
        return self.messages
    
    def _detect_encoding(self, file_path: str) -> str:
        """检测文件编码"""
        encodings = ['utf-8', 'gbk', 'ascii', 'latin1']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    f.read()
                return encoding
            except UnicodeDecodeError:
                continue
        
        return 'utf-8'  # 默认
    
    def _parse_can_message(self, line: str, line_num: int) -> Dict[str, Any]:
        """
        解析CAN消息行
        支持多种ASC格式，包括标准帧和扩展帧
        """
        # 格式1: 时间戳 通道 CAN_ID Rx/Tx d DLC 数据字节
        # 例: 0.000000 1  123             Rx   d 8 01 02 03 04 05 06 07 08
        # 扩展帧例: 0.000000 1  18FEF100x        Rx   d 8 01 02 03 04 05 06 07 08
        pattern1 = r'^\s*(\d+\.\d+)\s+(\d+)\s+([0-9A-Fa-f]+)x?\s+(Rx|Tx)\s+d\s+(\d+)\s+(.*)$'
        
        # 格式2: 时间戳 通道 CAN_ID Rx/Tx DLC 数据字节
        # 例: 0.100000 1 123 Rx 8 AA BB CC DD EE FF 00 11
        # 扩展帧例: 0.100000 1 18FEF100x Rx 8 AA BB CC DD EE FF 00 11
        pattern2 = r'^\s*(\d+\.\d+)\s+(\d+)\s+([0-9A-Fa-f]+)x?\s+(Rx|Tx)\s+(\d+)\s+(.*)$'
        
        # 格式3: CANoe格式 - 扩展帧有特殊标记
        # 例: 0.000000 1  18FEF100         Rx   d 8 01 02 03 04 05 06 07 08
        pattern3 = r'^\s*(\d+\.\d+)\s+(\d+)\s+([0-9A-Fa-f]{8})\s+(Rx|Tx)\s+d\s+(\d+)\s+(.*)$'
        
        # 尝试匹配格式1（支持扩展帧x标记）
        match = re.match(pattern1, line, re.IGNORECASE)
        if match:
            timestamp, channel, can_id, direction, dlc, data_str = match.groups()
            # 检查是否有 'x' 后缀标记（扩展帧标记），具体数值判断在 _create_message 中
            is_extended = line.find(can_id + 'x') != -1
            return self._create_message(timestamp, channel, can_id, direction, dlc, data_str, line_num, is_extended)
        
        # 尝试匹配格式2（支持扩展帧x标记）
        match = re.match(pattern2, line, re.IGNORECASE)
        if match:
            timestamp, channel, can_id, direction, dlc, data_str = match.groups()
            # 检查是否有 'x' 后缀标记（扩展帧标记），具体数值判断在 _create_message 中
            is_extended = line.find(can_id + 'x') != -1
            return self._create_message(timestamp, channel, can_id, direction, dlc, data_str, line_num, is_extended)
        
        # 尝试匹配格式3（8位十六进制通常是扩展帧）
        match = re.match(pattern3, line, re.IGNORECASE)
        if match:
            timestamp, channel, can_id, direction, dlc, data_str = match.groups()
            is_extended = True  # 8位十六进制默认为扩展帧
            return self._create_message(timestamp, channel, can_id, direction, dlc, data_str, line_num, is_extended)
        
        return None
    
    def _create_message(self, timestamp: str, channel: str, can_id: str, 
                       direction: str, dlc: str, data_str: str, line_num: int, is_extended: bool = False) -> Dict[str, Any]:
        """创建消息字典"""
        try:
            # 清理CAN ID（移除可能的x后缀）
            clean_can_id = can_id.rstrip('x').rstrip('X')
            
            # 解析数据字节
            data_bytes = []
            if data_str.strip():
                hex_values = data_str.strip().split()
                for hex_val in hex_values:
                    if len(hex_val) <= 2:  # 确保是有效的十六进制
                        try:
                            data_bytes.append(int(hex_val, 16))
                        except ValueError:
                            break
            
            # 转换CAN ID为整数
            can_id_int = int(clean_can_id, 16)
            
            # 自动检测扩展帧（如果没有明确指定）
            if not is_extended:
                # 标准帧: 0x000 - 0x7FF (0-2047)
                # 扩展帧: 0x000 - 0x1FFFFFFF (0-536870911)
                # 如果CAN ID > 0x7FF (2047)，则认为是扩展帧
                is_extended = can_id_int > 0x7FF
            
            return {
                'timestamp': float(timestamp),
                'channel': int(channel),
                'can_id': can_id_int,  # 转换为十进制
                'can_id_hex': clean_can_id.upper(),
                'is_extended': is_extended,
                'frame_type': 'Extended' if is_extended else 'Standard',
                'direction': direction,
                'dlc': int(dlc),
                'data': data_bytes,
                'data_hex': ' '.join(f'{b:02X}' for b in data_bytes),
                'line_number': line_num,
                'raw_line': line_num
            }
        except (ValueError, TypeError) as e:
            print(f"⚠️ 解析消息失败 (行{line_num}): {e}")
            return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        if not self.messages:
            return {}
        
        # 基本统计
        total_messages = len(self.messages)
        unique_can_ids = len(set(msg['can_id'] for msg in self.messages))
        
        # 时间统计
        timestamps = [msg['timestamp'] for msg in self.messages]
        time_start = min(timestamps)
        time_end = max(timestamps)
        duration = time_end - time_start
        
        # CAN ID统计
        can_id_counts = {}
        for msg in self.messages:
            can_id = msg['can_id']
            can_id_counts[can_id] = can_id_counts.get(can_id, 0) + 1
        
        # 方向统计
        rx_count = sum(1 for msg in self.messages if msg['direction'].upper() == 'RX')
        tx_count = sum(1 for msg in self.messages if msg['direction'].upper() == 'TX')
        
        return {
            'total_messages': total_messages,
            'unique_can_ids': unique_can_ids,
            'time_start': time_start,
            'time_end': time_end,
            'duration_seconds': duration,
            'frequency_hz': total_messages / duration if duration > 0 else 0,
            'rx_messages': rx_count,
            'tx_messages': tx_count,
            'can_id_counts': dict(sorted(can_id_counts.items(), key=lambda x: x[1], reverse=True)),
            'most_frequent_can_id': max(can_id_counts.items(), key=lambda x: x[1]) if can_id_counts else None,
        }
    
    def filter_by_can_id(self, can_id: int) -> List[Dict[str, Any]]:
        """按CAN ID过滤消息"""
        return [msg for msg in self.messages if msg['can_id'] == can_id]
    
    def filter_by_time_range(self, start_time: float, end_time: float) -> List[Dict[str, Any]]:
        """按时间范围过滤消息"""
        return [msg for msg in self.messages if start_time <= msg['timestamp'] <= end_time]
    
    def export_to_csv(self, output_path: str) -> bool:
        """导出为CSV格式"""
        try:
            import csv
            
            with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
                if not self.messages:
                    return False
                
                # CSV头部
                fieldnames = ['timestamp', 'channel', 'can_id_hex', 'direction', 'dlc', 'data_hex']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                # 写入数据
                for msg in self.messages:
                    writer.writerow({
                        'timestamp': msg['timestamp'],
                        'channel': msg['channel'],
                        'can_id_hex': f"0x{msg['can_id']:X}",
                        'direction': msg['direction'],
                        'dlc': msg['dlc'],
                        'data_hex': msg['data_hex']
                    })
            
            print(f"✅ CSV导出成功: {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ CSV导出失败: {e}")
            return False

def demo_read_asc():
    """演示ASC文件读取"""
    print("🎯 ASC文件读取演示")
    print("="*50)
    
    # 创建读取器
    reader = SimpleASCReader()
    
    # 读取文件
    try:
        messages = reader.read_file("sample_data.asc")
        
        if not messages:
            print("❌ 没有解析到CAN消息")
            return
        
        # 显示基本信息
        print(f"\n📊 解析结果:")
        print(f"   总消息数: {len(messages)}")
        
        # 显示前几条消息
        print(f"\n📋 前5条消息:")
        for i, msg in enumerate(messages[:5]):
            print(f"   {i+1}. [{msg['timestamp']:.3f}s] CAN_ID:0x{msg['can_id']:X} "
                  f"{msg['direction']} DLC:{msg['dlc']} 数据:[{msg['data_hex']}]")
        
        # 统计信息
        stats = reader.get_statistics()
        print(f"\n📈 统计信息:")
        print(f"   唯一CAN ID: {stats['unique_can_ids']}")
        print(f"   时间跨度: {stats['duration_seconds']:.3f}秒")
        print(f"   平均频率: {stats['frequency_hz']:.2f}Hz")
        print(f"   RX消息: {stats['rx_messages']} 条")
        print(f"   TX消息: {stats['tx_messages']} 条")
        
        # 显示CAN ID分布
        if stats['can_id_counts']:
            print(f"\n🎯 CAN ID分布:")
            for can_id, count in list(stats['can_id_counts'].items())[:5]:
                print(f"   0x{can_id:X}: {count} 条消息")
        
        # 过滤示例
        if stats['can_id_counts']:
            most_freq_id = list(stats['can_id_counts'].keys())[0]
            filtered = reader.filter_by_can_id(most_freq_id)
            print(f"\n🔍 过滤CAN ID 0x{most_freq_id:X}: {len(filtered)} 条消息")
        
        # 导出示例
        if reader.export_to_csv("output.csv"):
            print(f"📤 已导出到: output.csv")
        
    except Exception as e:
        print(f"❌ 读取失败: {e}")

if __name__ == "__main__":
    demo_read_asc()