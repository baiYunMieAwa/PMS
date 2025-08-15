import struct
from protocol import MCField, VarInt
import json
from typing import List, Dict, Union


def convert_mc_format(text: str) -> List[Dict[str, Union[str, bool]]]:
    """
    将包含 & 格式代码的字符串转换为 Minecraft JSON 聊天格式

    格式代码：
    &0 - 黑色        &8 - 深灰色
    &1 - 深蓝色      &9 - 蓝色
    &2 - 深绿色      &a - 绿色
    &3 - 深青色      &b - 青色
    &4 - 深红色      &c - 红色
    &5 - 紫色        &d - 粉红色
    &6 - 金色        &e - 黄色
    &7 - 灰色        &f - 白色

    格式代码：
    &l - 粗体        &o - 斜体
    &n - 下划线       &m - 删除线
    &k - 模糊文字     &r - 重置格式

    参数:
    text (str): 包含 & 格式代码的输入字符串

    返回:
    List[Dict]: Minecraft JSON 聊天格式数组
    """
    # 颜色代码映射
    color_map = {
        '0': 'black', '1': 'dark_blue', '2': 'dark_green', '3': 'dark_aqua',
        '4': 'dark_red', '5': 'dark_purple', '6': 'gold', '7': 'gray',
        '8': 'dark_gray', '9': 'blue', 'a': 'green', 'b': 'aqua',
        'c': 'red', 'd': 'light_purple', 'e': 'yellow', 'f': 'white',
        'r': 'reset'  # 特殊处理
    }

    # 格式代码映射
    format_map = {
        'l': 'bold',
        'o': 'italic',
        'n': 'underlined',
        'm': 'strikethrough',
        'k': 'obfuscated'
    }

    # 结果列表和当前文本段
    result: List[Dict[str, Union[str, bool]]] = []
    current_segment = {"text": ""}

    # 当前样式状态
    current_color = None
    current_formats = {
        'bold': False,
        'italic': False,
        'underlined': False,
        'strikethrough': False,
        'obfuscated': False
    }

    i = 0
    while i < len(text):
        if text[i] == '&' and i + 1 < len(text):
            # 处理格式代码
            code_char = text[i + 1].lower()

            # 处理颜色代码
            if code_char in color_map:
                # 保存当前文本段（如果有内容）
                if current_segment["text"]:
                    result.append(current_segment.copy())
                    current_segment = {"text": ""}

                # 重置格式（如果是 &r）
                if code_char == 'r':
                    current_color = None
                    for key in current_formats:
                        current_formats[key] = False
                else:
                    current_color = color_map[code_char]

                # 应用当前颜色
                if current_color and current_color != 'reset':
                    current_segment["color"] = current_color

                # 应用当前格式
                for fmt, active in current_formats.items():
                    if active:
                        current_segment[fmt] = True

                # 跳过两个字符 (& 和代码)
                i += 2
                continue

            # 处理格式代码
            elif code_char in format_map:
                # 保存当前文本段（如果有内容）
                if current_segment["text"]:
                    result.append(current_segment.copy())
                    current_segment = {"text": ""}

                # 切换格式状态
                format_name = format_map[code_char]
                current_formats[format_name] = not current_formats[format_name]

                # 应用当前颜色
                if current_color:
                    current_segment["color"] = current_color

                # 应用当前格式
                for fmt, active in current_formats.items():
                    if active:
                        current_segment[fmt] = True

                # 跳过两个字符 (& 和代码)
                i += 2
                continue

        # 普通字符，添加到当前文本段
        current_segment["text"] += text[i]
        i += 1

    # 添加最后一个文本段
    if current_segment["text"]:
        result.append(current_segment)

    return result


def pretty_print_json(result: List[Dict]) -> str:
    """美化输出 JSON 格式"""
    # 如果只有一个元素，直接返回其 JSON
    if len(result) == 1:
        return json.dumps(result[0], ensure_ascii=False)

    # 多个元素返回数组
    return json.dumps(result, ensure_ascii=False, indent=2)


class Bool(MCField):
    def __init__(self, tf):
        if tf:
            self.sendData = bytearray([1])
        else:
            self.sendData = bytearray([0])

    @property
    def data(self):
        return self.sendData


class Any(MCField):
    def __init__(self, a):
        self.sendData = a

    @property
    def data(self):
        return self.sendData


def Int(a):
    return Any(bytearray(struct.pack(">i", a)))


def Long(a):
    return Any(bytearray(struct.pack(">q", a)))


def Double(a):
    return Any(bytearray(struct.pack(">d", a)))


def Float(a):
    return Any(bytearray(struct.pack(">f", a)))


def encode_varint(a):
    return VarInt(a).data
