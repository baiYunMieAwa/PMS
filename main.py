import random
import time
from protocol import *
from socket import socket as Socket
from _thread import start_new_thread


# 0: 握手, 1: 查询, 2: 登录, 3: 游玩
state = 0
player_name = ""


# noinspection PyBroadException
def heartbeat_packet(session):
    global state
    try:
        while True:
            if state == 3:
                np = Packet(0x21)
                np.addField(Long(random.randint(0, 10**10)))
                session.sendPacket(np)
                # print("发送 心跳包")
                time.sleep(10)
    except:
        print("切换 握手阶段")
        state = 0
        return


def mc_join_game(EID, gameMode=0, world=0, seed=0, worldType="default", vd=8):
    np = Packet(0x26)
    np.addField(Int(EID))  # 玩家的实体 ID （EID）
    np.addField(UnsignedByte(gameMode))  # 0: 生存, 1: 创造, 2: 冒险, 3: 旁观者. 第3位 (0x8) 是极限模式标志
    np.addField(Int(world))  # -1: 下界，0: 主世界，1: 末地. 请注意, 这不是 VarInt, 而是一个常规 int
    np.addField(Long(seed))  # 世界种子的 SHA-256 哈希的前 8 个字节
    np.addField(UnsignedByte(20))  # 最大玩家数, 曾经被客户端用来绘制玩家列表，但现在被忽略了
    np.addField(MCString(worldType))  # 世界类型: default, flat, largeBiomes, amplified, customized, buffet, default_1_1
    np.addField(VarInt(vd))  # 视距
    np.addField(Bool(True))  # 是否减少调试信息
    np.addField(Bool(True))  # 是否启用重生屏幕
    session.sendPacket(np)


def mc_add_player():
    pass


def mc_print(text):
    chat = f'{{"extra":{str(convert_mc_format(text)).replace("'", '"')},"text":""}}'
    np = Packet(0x0f)
    np.addField(MCString(chat))
    np.addField(Byte(1))
    session.sendPacket(np)
    print(f"发送 聊天消息({chat})")


def mc_set_location(x, y, z, yaw=0.0, pitch=0.0):
    pos_packet = Packet(0x36)
    pos_packet.addField(Double(float(x)))  # X
    pos_packet.addField(Double(float(y)))  # Y (安全高度)
    pos_packet.addField(Double(float(z)))  # Z
    pos_packet.addField(Float(float(yaw)))  # Yaw
    pos_packet.addField(Float(float(pitch)))  # Pitch
    pos_packet.addField(Byte(0))  # 标志
    # 这(上方)是一个位掩码, X/Y/Z/Y_ROT/X_ROT. 如果设置了X, x值是相对的而不是绝对的(偏移值)
    """
    X 0x01
    Y 0x02
    Z 0x04
    Y_ROT 0x08
    X_ROT 0x10
    """
    pos_packet.addField(VarInt(random.randint(-10000, 10000)))  # 传送ID
    session.sendPacket(pos_packet)


def onPacketRecv(packet: Packet):
    global state
    global player_name
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
        player_name = packet[0]

        np = Packet(2)
        uuid = "530fa97a-357f-3c19-94d3-0c5c65c18fe8"
        np.addField(MCString(uuid))
        np.addField(MCString(player_name))
        session.sendPacket(np)

        print("切换 游玩状态")
        state = 3

        # 发送加入游戏数据包
        mc_join_game(0, 1, world=0, seed=72623859790382856, worldType="flat", vd=8)

        # 发送玩家加入游戏消息
        mc_print(f"&e{player_name} 加入了游戏")

        # 发送玩家位置和视角数据包
        mc_set_location(0, 64, 0)

    elif state == 3:
        if packet.data[1] == 0x03:
            chat = packet.parse([MCString])[0].get()
            print(f"收到 客户端聊天消息({chat})")
            if chat[0] == "/":
                command = chat[1:].split(" ")
                if command[0] == "say":
                    mc_print(f"[{player_name}] {" ".join(command[1:])}")
                else:
                    mc_print(f"命令: {command}")
            else:
                mc_print(chat)


host = "127.0.0.1"
port = 25566
s = Socket()
s.bind((host, port))
s.listen(5)                 # 等待客户端连接

while True:

    c, addr = s.accept()     # 建立客户端连接
    session = Session(c, onPacketRecv)
    print(f'连接地址: {addr}')
    # noinspection PyBroadException
    start_new_thread(heartbeat_packet, (session,))

# \x18&\x00\x01\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\x14\x04flat\x08\x00\x00
