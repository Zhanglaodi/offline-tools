#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dbcmini.py — 极简 DBC 编写工具（Message/Signal 增删改、自动范围推算、导出）
Usage: python dbcmini.py
"""

from dataclasses import dataclass, field
from typing import List, Optional

# -------------------- 数据结构 --------------------

@dataclass
class Signal:
    name: str
    start_bit: int                   # 起始位（0-63）
    length: int                      # 位长（1-64）
    intel_little_endian: bool = True # True: Intel(@1), False: Motorola(@0)
    signed: bool = False             # True: 有符号(-)，False: 无符号(+)
    factor: float = 1.0
    offset: float = 0.0
    minimum: float = 0.0
    maximum: float = 0.0
    unit: str = ""
    receivers: List[str] = field(default_factory=lambda: ["Vector__XXX"])
    is_multiplexer: bool = False     # 简化：占位，不展开多路复用细节
    multiplexer_switch_value: int = 0

    def to_dbc(self) -> str:
        endian_flag = "1" if self.intel_little_endian else "0"  # @1 Intel(LE), @0 Motorola(BE)
        sign_flag = "-" if self.signed else "+"
        recv = ",".join(self.receivers) if self.receivers else "Vector__XXX"
        mux_part = f" m{self.multiplexer_switch_value}" if self.is_multiplexer else ""
        return (f' SG_ {self.name}{mux_part} : {self.start_bit}|{self.length}'
                f'@{endian_flag}{sign_flag} ({self.factor},{self.offset})'
                f' [{self.minimum}|{self.maximum}] "{self.unit}" {recv}')

@dataclass
class Message:
    can_id: int               # 0x00000000 - 0x1FFFFFFF
    name: str
    dlc: int                  # 0-8（经典 CAN）
    transmitter: str = "ECU"
    signals: List[Signal] = field(default_factory=list)
    is_extended: bool = False # 标注用途；导出仍用标准 DBC 格式

    def to_dbc(self) -> str:
        head = f"BO_ {self.can_id} {self.name}: {self.dlc} {self.transmitter}"
        sigs = "\n".join(s.to_dbc() for s in self.signals)
        return head + ("\n" + sigs if sigs else "")

# -------------------- 项目与导出 --------------------

DEFAULT_NS = [
    "NS_DESC_", "CM_", "BA_DEF_", "BA_", "VAL_", "CAT_DEF_", "CAT_",
    "FILTER", "BA_DEF_DEF_", "EV_DATA_", "ENVVAR_DATA_", "SGTYPE_",
    "SGTYPE_VAL_", "BA_DEF_SGTYPE_", "BA_SGTYPE_", "SIG_TYPE_REF_",
    "VAL_TABLE_", "SIG_GROUP_", "SIG_VALTYPE_", "SIGTYPE_VALTYPE_",
    "BO_TX_BU_", "BA_DEF_REL_", "BA_REL_", "BA_DEF_DEF_REL_",
    "BU_SG_REL_", "BU_EV_REL_", "BU_BO_REL_", "SG_MUL_VAL_"
]

class DBCProject:
    def __init__(self):
        self.version = "1.0"
        self.nodes: List[str] = ["ECU", "Vector__XXX"]
        self.messages: List[Message] = []

    # --- 增查 ---

    def add_node(self, name: str):
        if name and name not in self.nodes:
            self.nodes.append(name)

    def add_message(self, can_id: int, name: str, dlc: int, tx: str = "ECU", extended: bool=False) -> Message:
        m = Message(can_id=can_id, name=name, dlc=dlc, transmitter=tx, is_extended=extended)
        self.messages.append(m)
        self.add_node(tx)
        return m

    def find_message(self, name_or_id: str) -> Optional[Message]:
        # 先按名字
        for m in self.messages:
            if m.name == name_or_id:
                return m
        # 再按 ID（十进制或 0x...）
        try:
            cid = int(name_or_id, 16) if name_or_id.lower().startswith("0x") else int(name_or_id)
            for m in self.messages:
                if m.can_id == cid:
                    return m
        except Exception:
            pass
        return None

    # --- 导出 ---

    def to_dbc_text(self) -> str:
        lines = []
        lines.append(f'VERSION "{self.version}"\n')
        lines.append("NS_:")
        for ns in DEFAULT_NS:
            lines.append(f'  {ns}')
        lines.append("\nBS_:\n")
        nodes_line = " ".join(self.nodes) if self.nodes else ""
        lines.append(f"BU_: {nodes_line}\n")
        for m in self.messages:
            lines.append(m.to_dbc() + "\n")
        return "\n".join(lines).rstrip() + "\n"

    def save(self, path: str):
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_dbc_text())

# -------------------- 交互工具函数 --------------------

HELP = """
命令：
  help                         显示帮助
  list                         列出所有消息和信号（信号含索引）
  add_node <name>              添加节点
  add_msg                      交互新增消息（ID/名称/DLC/发送节点）
  add_sig                      交互为某消息添加信号
  edit_msg                     交互修改消息字段
  del_msg                      交互删除消息
  edit_sig                     交互修改信号字段
  del_sig                      交互删除信号
  move_sig                     在同一消息内调整信号顺序
  save <file.dbc>              导出为 DBC 文件
  quit                         退出

说明：
- Endian：@1 表示 Intel 小端(LE)；@0 表示 Motorola 大端(BE)。
- Sign：+ 无符号，- 有符号（补码）。
- start_bit/length 采用标准 DBC 位编号（bit0 为最低位）。
"""

def input_int(prompt: str, base10: bool=True, allow_hex: bool=True, default=None):
    while True:
        s = input(prompt).strip()
        if not s and default is not None:
            return default
        try:
            if allow_hex and s.lower().startswith("0x"):
                return int(s, 16)
            return int(s, 10 if base10 else 10)
        except Exception:
            print("请输入整数（支持 0x 十六进制）。")

def input_float(prompt: str, default=None):
    while True:
        s = input(prompt).strip()
        if not s and default is not None:
            return default
        try:
            return float(s)
        except Exception:
            print("请输入数值。")

def yesno(prompt: str, default_yes=True):
    s = input(prompt + (" (Y/n): " if default_yes else " (y/N): ")).strip().lower()
    if not s:
        return default_yes
    return s.startswith("y")

def choose_message(proj: DBCProject) -> Optional[Message]:
    target = input("目标消息（名称或ID/0xID）: ").strip()
    m = proj.find_message(target)
    if not m:
        print("未找到该消息。")
    return m

def choose_signal(m: Message) -> int:
    if not m.signals:
        print("该消息无信号。")
        return -1
    for i, s in enumerate(m.signals):
        endian = "@1" if s.intel_little_endian else "@0"
        sign = "-" if s.signed else "+"
        print(f"[{i}] {s.name}  start={s.start_bit} len={s.length} {endian}{sign}")
    idx = input_int("选择信号索引: ")
    if idx < 0 or idx >= len(m.signals):
        print("索引越界。")
        return -1
    return idx

# -------------------- 自动范围推算 --------------------

def compute_phys_range(length: int, signed: bool, factor: float, offset: float):
    if length <= 0 or length > 64:
        raise ValueError("length 必须在 1..64")
    if signed:
        raw_min = -(1 << (length - 1))
        raw_max =  (1 << (length - 1)) - 1
    else:
        raw_min = 0
        raw_max = (1 << length) - 1
    phys_min = round(raw_min * factor + offset, 6)
    phys_max = round(raw_max * factor + offset, 6)
    return phys_min, phys_max

# -------------------- 交互命令实现 --------------------

def add_msg_interactive(proj: DBCProject):
    cid = input_int("CAN ID（支持0x前缀）: ")
    name = input("消息名称: ").strip()
    dlc  = input_int("DLC（0-8）: ")
    tx   = input("发送节点（默认 ECU）: ").strip() or "ECU"
    ext  = (input("扩展帧？(y/N): ").strip().lower() == "y")
    m = proj.add_message(can_id=cid, name=name, dlc=dlc, tx=tx, extended=ext)
    print(f"已添加消息：{m.name} (ID={hex(m.can_id)}, DLC={m.dlc}, TX={m.transmitter})")

def add_sig_interactive(proj: DBCProject):
    m = choose_message(proj)
    if not m:
        return
    name = input("信号名称: ").strip()
    start = input_int("起始位 start_bit（0-63）: ")
    length = input_int("位长 length（1-64）: ")
    endian = input("字节序 Intel小端？(Y/n，@1=Intel, @0=Motorola): ").strip().lower()
    intel = (endian != "n")
    signed = (input("有符号？(y/N): ").strip().lower() == "y")
    factor = input_float("比例系数 factor（默认1）: ", 1.0)
    offset = input_float("偏移 offset（默认0）: ", 0.0)

    # 自动推算 min/max
    auto_mm = input("自动推算 min/max ？(Y/n): ").strip().lower()
    if auto_mm != "n":
        try:
            minimum, maximum = compute_phys_range(length, signed, factor, offset)
            print(f"→ 自动推算范围: [{minimum} .. {maximum}]")
        except Exception as e:
            print(f"自动推算失败：{e}，请手动输入。")
            minimum = input_float("最小值 min（默认0）: ", 0.0)
            maximum = input_float("最大值 max（默认0）: ", 0.0)
    else:
        minimum = input_float("最小值 min（默认0）: ", 0.0)
        maximum = input_float("最大值 max（默认0）: ", 0.0)

    unit = input('单位 unit（可空，示例 "km/h"）: ').strip()
    recvs_line = input("接收节点（逗号分隔，默认 Vector__XXX）: ").strip()
    recvs = [r.strip() for r in recvs_line.split(",") if r.strip()] if recvs_line else ["Vector__XXX"]

    s = Signal(
        name=name, start_bit=start, length=length,
        intel_little_endian=intel, signed=signed,
        factor=factor, offset=offset,
        minimum=minimum, maximum=maximum,
        unit=unit, receivers=recvs
    )
    m.signals.append(s)
    print(f"已为消息 {m.name} 添加信号：{s.name}")

def list_all(proj: DBCProject):
    if not proj.messages:
        print("暂无消息。")
        return
    for m in proj.messages:
        print(f"- BO_ {hex(m.can_id)} {m.name}: DLC={m.dlc}, TX={m.transmitter}, SIGS={len(m.signals)}")
        for i, s in enumerate(m.signals):
            print(f"    [{i}] " + s.to_dbc())

def edit_msg_interactive(proj: DBCProject):
    m = choose_message(proj)
    if not m:
        return
    print(f"当前：ID={hex(m.can_id)} name={m.name} dlc={m.dlc} tx={m.transmitter} ext={m.is_extended}")
    if yesno("修改 CAN ID？"):     m.can_id = input_int("新 CAN ID（支持0x）: ")
    if yesno("修改 名称？"):       m.name = input("新名称: ").strip() or m.name
    if yesno("修改 DLC？"):        m.dlc = input_int("新 DLC（0-8）: ")
    if yesno("修改 发送节点？"):
        m.transmitter = input("新发送节点: ").strip() or m.transmitter
        proj.add_node(m.transmitter)
    if yesno("修改 扩展帧标志？"):
        m.is_extended = yesno("设为扩展帧？", default_yes=m.is_extended)
    print("消息已更新。")

def del_msg_interactive(proj: DBCProject):
    m = choose_message(proj)
    if not m:
        return
    if yesno(f"确认删除消息 {m.name} 及其所有信号？", default_yes=False):
        proj.messages = [x for x in proj.messages if x is not m]
        print("已删除。")

def edit_sig_interactive(proj: DBCProject):
    m = choose_message(proj)
    if not m:
        return
    idx = choose_signal(m)
    if idx < 0:
        return
    s = m.signals[idx]
    print(f"当前：{s.name} start={s.start_bit} len={s.length} endian={'Intel(@1)' if s.intel_little_endian else 'Motorola(@0)'} sign={'signed' if s.signed else 'unsigned'}")
    print(f"缩放 factor={s.factor} offset={s.offset} range=[{s.minimum},{s.maximum}] unit=\"{s.unit}\" recv={','.join(s.receivers)}")

    if yesno("修改 名称？"):          s.name = input("新名称: ").strip() or s.name
    if yesno("修改 起始位？"):        s.start_bit = input_int("新 start_bit: ")
    if yesno("修改 位长？"):          s.length = input_int("新 length: ")
    if yesno("修改 字节序？"):        s.intel_little_endian = yesno("Intel小端(@1)？", default_yes=s.intel_little_endian)
    if yesno("修改 有符号？"):        s.signed = yesno("设为有符号？", default_yes=s.signed)
    if yesno("修改 缩放参数（factor/offset）？"):
        s.factor = input_float("factor: ", s.factor)
        s.offset = input_float("offset: ", s.offset)
        if yesno("按新缩放自动重算 min/max？"):
            mn, mx = compute_phys_range(s.length, s.signed, s.factor, s.offset)
            print(f"→ 自动范围: [{mn} .. {mx}]")
            s.minimum, s.maximum = mn, mx
    if yesno("修改 最小值？"):        s.minimum = input_float("min: ", s.minimum)
    if yesno("修改 最大值？"):        s.maximum = input_float("max: ", s.maximum)
    if yesno("修改 单位？"):          s.unit = input('unit（可空）: ').strip()
    if yesno("修改 接收节点？"):
        line = input("接收节点（逗号分隔）: ").strip()
        s.receivers = [x.strip() for x in line.split(",")] if line else s.receivers
        for n in s.receivers:
            proj.add_node(n)
    print("信号已更新。")

def del_sig_interactive(proj: DBCProject):
    m = choose_message(proj)
    if not m:
        return
    idx = choose_signal(m)
    if idx < 0:
        return
    s = m.signals[idx]
    if yesno(f"确认删除信号 {s.name}？", default_yes=False):
        m.signals.pop(idx)
        print("已删除。")

def move_sig_interactive(proj: DBCProject):
    m = choose_message(proj)
    if not m:
        return
    idx = choose_signal(m)
    if idx < 0:
        return
    new_idx = input_int("移动到的新索引: ")
    if new_idx < 0 or new_idx >= len(m.signals):
        print("新索引越界。")
        return
    sig = m.signals.pop(idx)
    m.signals.insert(new_idx, sig)
    print("已调整顺序。")

# -------------------- 主循环 --------------------

def main():
    proj = DBCProject()
    print("== DBC Mini 工具（Message/Signal 增删改 & 自动范围）==")
    print(HELP)
    while True:
        try:
            cmd = input("dbc> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break

        if not cmd:
            continue
        if cmd == "help":
            print(HELP)
        elif cmd == "list":
            list_all(proj)
        elif cmd.startswith("add_node"):
            parts = cmd.split()
            if len(parts) >= 2:
                proj.add_node(parts[1])
                print(f"已添加节点：{parts[1]}")
            else:
                print("用法：add_node <name>")
        elif cmd == "add_msg":
            add_msg_interactive(proj)
        elif cmd == "add_sig":
            add_sig_interactive(proj)
        elif cmd == "edit_msg":
            edit_msg_interactive(proj)
        elif cmd == "del_msg":
            del_msg_interactive(proj)
        elif cmd == "edit_sig":
            edit_sig_interactive(proj)
        elif cmd == "del_sig":
            del_sig_interactive(proj)
        elif cmd == "move_sig":
            move_sig_interactive(proj)
        elif cmd.startswith("save"):
            parts = cmd.split(maxsplit=1)
            if len(parts) == 2:
                proj.save(parts[1])
                print(f"已保存：{parts[1]}")
            else:
                print("用法：save <file.dbc>")
        elif cmd in ("quit", "exit"):
            print("Bye.")
            break
        else:
            print("未知命令，输入 help 查看。")

if __name__ == "__main__":
    main()
