import random
import time
from io import BytesIO
from protocol import *
from socket import socket as Socket
import struct
import nbtlib
from nbtlib import serialize_tag


# 0: 握手, 1: 查询, 2: 登录, 3: 游玩
state = 0


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


def mc_print(text, color="white"):
    chat = f'{{"extra":[{{"text":"{text}", "color":"{color}"}}],"text":""}}'
    # 官方: \x0f0{"extra":[{"text":"test awa"}],"text":""}\x01
    # 我:  $\x0f{"extra":[{"text":"test awa"}],"text":""}\x01
    np = Packet(0x0f)
    np.addField(MCString(chat))
    np.addField(Byte(1))
    session.sendPacket(np)
    print(f"发送 聊天消息({chat})")


def onPacketRecv(packet: Packet):
    global state
    if state == 0:
        print("收到 握手包")
        packet = [i.get() for i in packet.parse([VarInt, MCString, UnsignedShort, VarInt])]
        print(packet)
        if packet[-1] == 1:
            state = 1
            print("切换 查询阶段")
        elif packet[-1] == 2:
            state = 2
            print("切换 登录阶段")
    elif state == 1:
        if packet.data == bytearray(b'\x01\x00'):
            print("发送 服务器信息")
            np = Packet(0)
            np.addField(MCString(
                '{"description":{"text":"Test Server - make by Python"},"players":{"max":20,"online":0},"version":{"name":"Python 1.15.2","protocol":578}}'))
            session.sendPacket(np)
        elif packet.data[1] == 1:
            print("发送 ping包响应")
            session.sendPacket(packet)
            state = 0
            print("切换 握手阶段")
    elif state == 2:
        packet = [i.get() for i in packet.parse([MCString])]
        print(f"收到 玩家名({packet[0]})")

        np = Packet(2)
        uuid = "530fa97a-357f-3c19-94d3-0c5c65c18fe8"
        np.addField(MCString(uuid))
        np.addField(MCString(packet[0]))
        session.sendPacket(np)

        print("切换 游玩状态")
        state = 3

        np = Packet(0x26)
        np.addField(Int(0))                  # 玩家的实体 ID （EID）
        np.addField(UnsignedByte(1))            # 0: 生存, 1: 创造, 2: 冒险, 3: 旁观者. 第3位 (0x8) 是极限模式标志
        np.addField(Int(0))                     # -1: 下界，0: 主世界，1: 末地. 请注意, 这不是 VarInt, 而是一个常规 int
        np.addField(Long(72623859790382856))    # 世界种子的 SHA-256 哈希的前 8 个字节
        np.addField(UnsignedByte(20))           # 最大玩家数, 曾经被客户端用来绘制玩家列表，但现在被忽略了
        np.addField(MCString("flat"))           # 世界类型: default, flat, largeBiomes, amplified, customized, buffet, default_1_1
        np.addField(VarInt(8))                  # 视距
        np.addField(Bool(True))                 # 是否减少调试信息
        np.addField(Bool(True))                 # 是否启用重生屏幕
        session.sendPacket(np)

        # 发送空区块
        # chunk_packet = create_empty_chunk_packet(0, 0)
        # session.sendPacket(chunk_packet)

        # 发送玩家位置和视角数据包
        pos_packet = Packet(0x36)
        pos_packet.addField(Double(0.0))  # X
        pos_packet.addField(Double(64.0))  # Y (安全高度)
        pos_packet.addField(Double(0.0))  # Z
        pos_packet.addField(Float(0.0))  # Yaw
        pos_packet.addField(Float(0.0))  # Pitch
        pos_packet.addField(Byte(0))  # 标志
        pos_packet.addField(VarInt(0))  # 传送ID
        session.sendPacket(pos_packet)
    elif state == 3:
        print(f"收到 {packet.data}")
        if packet.data[1] == 0x03:
            chat = packet.parse([MCString])[0].get()
            print(f"收到 客户端聊天消息({chat})")
            if chat[0] == "/":
                mc_print("命令test通过")
            else:
                mc_print(chat)


host = "127.0.0.1"
port = 25566
s = Socket()
s.bind((host, port))
s.listen(5)                 # 等待客户端连接

while True:
    print("切换 握手阶段")
    state = 0
    c, addr = s.accept()     # 建立客户端连接
    session = Session(c, onPacketRecv)
    print(f'连接地址: {addr}')
    # noinspection PyBroadException
    try:
        while True:
            if state == 3:
                np = Packet(0x21)
                np.addField(Long(random.randint(0, 10**10)))
                session.sendPacket(np)
            elif state == 0:
                break
            time.sleep(1)
    except:
        pass

# \x18&\x00\x01\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\x14\x04flat\x08\x00\x00
