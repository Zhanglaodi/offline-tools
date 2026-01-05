#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DBC文件解析器
支持CAN数据库文件解析，提取信号定义信息
"""

import re
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

@dataclass
class DBCSignal:
    """DBC信号定义"""
    name: str
    start_bit: int
    length: int
    byte_order: str  # 'big_endian' or 'little_endian'
    value_type: str  # 'signed' or 'unsigned'
    factor: float
    offset: float
    minimum: float
    maximum: float
    unit: str
    receivers: List[str]
    comment: str = ""
    value_table: Dict[int, str] = None

@dataclass
class DBCMessage:
    """DBC消息定义"""
    can_id: int
    name: str
    dlc: int
    transmitter: str
    signals: List[DBCSignal]
    comment: str = ""
    cycle_time: int = 0  # 周期时间(ms)
    is_extended: bool = False  # 是否为扩展帧

@dataclass
class DBCNode:
    """DBC节点定义"""
    name: str
    comment: str = ""

class DBCParser:
    """DBC文件解析器"""
    
    # 扩展帧标记位（DBC 文件中扩展帧 ID = 实际ID + 0x80000000）
    EXTENDED_FRAME_FLAG = 0x80000000
    
    def __init__(self):
        self.nodes: List[DBCNode] = []
        self.messages: List[DBCMessage] = []
        self.value_tables: Dict[str, Dict[int, str]] = {}
        self.attributes: Dict[str, Any] = {}
        self.comments: Dict[str, str] = {}
    
    @staticmethod
    def _convert_raw_can_id(raw_id: int) -> tuple:
        """
        转换原始 CAN ID 为实际 ID 和扩展帧标记
        
        DBC 文件中扩展帧的两种编码方式：
        1. 标准方式：actual_id + 0x80000000
        2. 简化方式：直接写 actual_id（某些工具）
        
        标准帧范围：0x000 - 0x7FF (0-2047)
        扩展帧范围：0x000 - 0x1FFFFFFF (0-536870911)
        
        Args:
            raw_id: DBC 文件中的原始 CAN ID
            
        Returns:
            (actual_id, is_extended): 实际 CAN ID 和是否为扩展帧
        """
        if raw_id >= DBCParser.EXTENDED_FRAME_FLAG:
            # 标准扩展帧编码：ID + 0x80000000
            is_extended = True
            actual_id = raw_id - DBCParser.EXTENDED_FRAME_FLAG
        elif raw_id > 0x7FF:
            # 简化扩展帧编码：直接写实际 ID（超过标准帧范围视为扩展帧）
            is_extended = True
            actual_id = raw_id
        else:
            # 标准帧：0x000 - 0x7FF
            is_extended = False
            actual_id = raw_id
        
        return actual_id, is_extended
    
    def parse_file(self, file_path: str) -> bool:
        """
        解析DBC文件
        
        Args:
            file_path: DBC文件路径
            
        Returns:
            解析是否成功
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"DBC文件不存在: {file_path}")
        
        print(f"📁 解析DBC文件: {file_path}")
        
        try:
            # 检测编码
            encoding = self._detect_encoding(file_path)
            print(f"🔤 检测编码: {encoding}")
            
            # 读取文件
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            
            # 清空之前的数据
            self.nodes.clear()
            self.messages.clear()
            self.value_tables.clear()
            self.attributes.clear()
            self.comments.clear()
            
            # 解析各个部分
            self._parse_nodes(content)
            self._parse_value_tables(content)
            self._parse_messages(content)
            self._parse_comments(content)
            self._parse_attributes(content)
            
            print(f"✅ DBC解析完成:")
            print(f"   节点数: {len(self.nodes)}")
            print(f"   消息数: {len(self.messages)}")
            print(f"   信号数: {sum(len(msg.signals) for msg in self.messages)}")
            
            return True
            
        except Exception as e:
            print(f"❌ DBC解析失败: {e}")
            return False
    
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
    
    def _parse_nodes(self, content: str):
        """解析节点定义"""
        # BU_: Node1 Node2 Node3
        pattern = r'BU_:\s*(.*?)(?:\n|$)'
        match = re.search(pattern, content, re.MULTILINE)
        
        if match:
            nodes_line = match.group(1).strip()
            if nodes_line:
                node_names = nodes_line.split()
                for name in node_names:
                    self.nodes.append(DBCNode(name=name))
    
    def _parse_value_tables(self, content: str):
        """解析值表定义"""
        # VAL_TABLE_ TableName 0 "Value0" 1 "Value1" ;
        pattern = r'VAL_TABLE_\s+(\w+)\s+((?:\d+\s+"[^"]*"\s*)*);'
        
        for match in re.finditer(pattern, content, re.MULTILINE):
            table_name = match.group(1)
            values_str = match.group(2)
            
            # 解析值对
            value_pattern = r'(\d+)\s+"([^"]*)"'
            values = {}
            for value_match in re.finditer(value_pattern, values_str):
                key = int(value_match.group(1))
                value = value_match.group(2)
                values[key] = value
            
            self.value_tables[table_name] = values
    
    def _parse_messages(self, content: str):
        """解析消息和信号定义"""
        # BO_ 123 MessageName: 8 NodeName
        message_pattern = r'BO_\s+(\d+)\s+(\w+):\s*(\d+)\s+(\w+)'
        
        for msg_match in re.finditer(message_pattern, content, re.MULTILINE):
            can_id_raw = int(msg_match.group(1))
            msg_name = msg_match.group(2)
            dlc = int(msg_match.group(3))
            transmitter = msg_match.group(4)
            
            # 过滤特殊消息：VECTOR__INDEPENDENT_SIG_MSG (用于未绑定的独立信号)
            # 这类消息的 ID 通常是 0xC0000000 (3221225472) 或其他超出范围的值
            if 'INDEPENDENT_SIG_MSG' in msg_name or can_id_raw >= 0xC0000000:
                continue
            
            # 判断是否为扩展帧并提取实际的 CAN ID
            can_id, is_extended = self._convert_raw_can_id(can_id_raw)
            
            # 过滤无效的扩展帧 ID（超出扩展帧最大范围 0x1FFFFFFF）
            if is_extended and can_id > 0x1FFFFFFF:
                continue
            
            # 查找该消息的所有信号
            signals = self._parse_signals_for_message(content, msg_match.end())
            
            message = DBCMessage(
                can_id=can_id,
                name=msg_name,
                dlc=dlc,
                transmitter=transmitter,
                signals=signals,
                is_extended=is_extended
            )
            
            self.messages.append(message)
    
    def _parse_signals_for_message(self, content: str, start_pos: int) -> List[DBCSignal]:
        """解析消息的信号定义"""
        signals = []
        
        # 从消息定义后开始查找信号，直到下一个消息定义
        remaining_content = content[start_pos:]
        
        # 找到下一个BO_定义的位置，限制搜索范围
        next_msg_match = re.search(r'\nBO_', remaining_content)
        if next_msg_match:
            search_content = remaining_content[:next_msg_match.start()]
        else:
            search_content = remaining_content
        
        # SG_ SignalName : 0|8@1+ (1,0) [0|255] "unit" Receiver1,Receiver2
        signal_pattern = r'SG_\s+(\w+)\s*:\s*(\d+)\|(\d+)@([01])([+-])\s*\(([^,]+),([^)]+)\)\s*\[([^|]*)\|([^\]]*)\]\s*"([^"]*)"\s*([^\n]*)'
        
        for signal_match in re.finditer(signal_pattern, search_content, re.MULTILINE):
            signal_name = signal_match.group(1)
            start_bit = int(signal_match.group(2))
            length = int(signal_match.group(3))
            byte_order = 'little_endian' if signal_match.group(4) == '1' else 'big_endian'
            value_type = 'signed' if signal_match.group(5) == '-' else 'unsigned'
            factor = float(signal_match.group(6))
            offset = float(signal_match.group(7))
            minimum = float(signal_match.group(8)) if signal_match.group(8).strip() else 0.0
            maximum = float(signal_match.group(9)) if signal_match.group(9).strip() else 0.0
            unit = signal_match.group(10)
            receivers_str = signal_match.group(11).strip()
            receivers = [r.strip() for r in receivers_str.split(',') if r.strip()]
            
            signal = DBCSignal(
                name=signal_name,
                start_bit=start_bit,
                length=length,
                byte_order=byte_order,
                value_type=value_type,
                factor=factor,
                offset=offset,
                minimum=minimum,
                maximum=maximum,
                unit=unit,
                receivers=receivers
            )
            
            signals.append(signal)
        
        return signals
    
    def _parse_comments(self, content: str):
        """解析注释"""
        # CM_ "comment text";
        # CM_ BU_ NodeName "comment text";
        # CM_ BO_ 123 "comment text";
        # CM_ SG_ 123 SignalName "comment text";
        
        comment_patterns = [
            (r'CM_\s+BU_\s+(\w+)\s+"([^"]*)"\s*;', 'node'),
            (r'CM_\s+BO_\s+(\d+)\s+"([^"]*)"\s*;', 'message'),
            (r'CM_\s+SG_\s+(\d+)\s+(\w+)\s+"([^"]*)"\s*;', 'signal'),
            (r'CM_\s+"([^"]*)"\s*;', 'general')
        ]
        
        for pattern, comment_type in comment_patterns:
            for match in re.finditer(pattern, content, re.MULTILINE):
                if comment_type == 'node':
                    node_name = match.group(1)
                    comment = match.group(2)
                    for node in self.nodes:
                        if node.name == node_name:
                            node.comment = comment
                            break
                elif comment_type == 'message':
                    can_id_raw = int(match.group(1))
                    can_id, _ = self._convert_raw_can_id(can_id_raw)
                    comment = match.group(2)
                    for message in self.messages:
                        if message.can_id == can_id:
                            message.comment = comment
                            break
                elif comment_type == 'signal':
                    can_id_raw = int(match.group(1))
                    can_id, _ = self._convert_raw_can_id(can_id_raw)
                    signal_name = match.group(2)
                    comment = match.group(3)
                    for message in self.messages:
                        if message.can_id == can_id:
                            for signal in message.signals:
                                if signal.name == signal_name:
                                    signal.comment = comment
                                    break
                            break
    
    def _parse_attributes(self, content: str):
        """解析属性定义"""
        # BA_ "GenMsgCycleTime" BO_ 123 1000;
        attr_pattern = r'BA_\s+"([^"]+)"\s+BO_\s+(\d+)\s+([^;]+);'
        
        for match in re.finditer(attr_pattern, content, re.MULTILINE):
            attr_name = match.group(1)
            can_id_raw = int(match.group(2))
            can_id, _ = self._convert_raw_can_id(can_id_raw)
            attr_value = match.group(3).strip()
            
            if attr_name == "GenMsgCycleTime":
                # 设置消息周期时间
                for message in self.messages:
                    if message.can_id == can_id:
                        try:
                            message.cycle_time = int(attr_value)
                        except ValueError:
                            pass
                        break
    
    def get_message_by_id(self, can_id: int) -> Optional[DBCMessage]:
        """根据CAN ID获取消息定义"""
        for message in self.messages:
            if message.can_id == can_id:
                return message
        return None
    
    def get_signals_by_message_id(self, can_id: int) -> List[DBCSignal]:
        """根据CAN ID获取信号列表"""
        message = self.get_message_by_id(can_id)
        return message.signals if message else []
    
    def search_signals_by_name(self, name_pattern: str) -> List[tuple]:
        """根据名称模式搜索信号"""
        results = []
        pattern = re.compile(name_pattern, re.IGNORECASE)
        
        for message in self.messages:
            for signal in message.signals:
                if pattern.search(signal.name):
                    results.append((message, signal))
        
        return results
    
    def export_signal_list(self) -> List[Dict[str, Any]]:
        """导出信号列表（用于界面显示）"""
        signal_list = []
        
        for message in self.messages:
            for signal in message.signals:
                signal_info = {
                    'message_name': message.name,
                    'can_id': message.can_id,
                    'can_id_hex': f"0x{message.can_id:X}",
                    'is_extended': message.is_extended,
                    'signal_name': signal.name,
                    'start_bit': signal.start_bit,
                    'length': signal.length,
                    'byte_order': signal.byte_order,
                    'value_type': signal.value_type,
                    'factor': signal.factor,
                    'offset': signal.offset,
                    'minimum': signal.minimum,
                    'maximum': signal.maximum,
                    'unit': signal.unit,
                    'comment': signal.comment,
                    'cycle_time': message.cycle_time
                }
                signal_list.append(signal_info)
        
        return signal_list

def demo_dbc_parser():
    """DBC解析器演示"""
    print("🎯 DBC文件解析演示")
    print("="*50)
    
    # 创建解析器
    parser = DBCParser()
    
    # 这里需要一个实际的DBC文件路径
    dbc_file = "example.dbc"
    
    if os.path.exists(dbc_file):
        # 解析文件
        if parser.parse_file(dbc_file):
            # 显示解析结果
            print(f"\n📊 解析结果:")
            print(f"   节点数: {len(parser.nodes)}")
            print(f"   消息数: {len(parser.messages)}")
            
            # 显示前几个消息
            print(f"\n📋 消息列表:")
            for i, msg in enumerate(parser.messages[:5]):
                ext_flag = " (扩展帧)" if msg.is_extended else ""
                print(f"   {i+1}. {msg.name} (0x{msg.can_id:X}{ext_flag}) - {len(msg.signals)}个信号")
                for signal in msg.signals[:3]:  # 显示前3个信号
                    print(f"      • {signal.name}: {signal.start_bit}位, {signal.length}位长")
            
            # 搜索示例
            search_results = parser.search_signals_by_name("speed")
            print(f"\n🔍 搜索'speed'相关信号: {len(search_results)}个结果")
            
            # 导出信号列表
            signal_list = parser.export_signal_list()
            print(f"\n📤 导出信号列表: {len(signal_list)}个信号")
        
    else:
        print(f"❌ DBC文件不存在: {dbc_file}")
        print("💡 请提供一个有效的DBC文件路径进行测试")

if __name__ == "__main__":
    demo_dbc_parser()