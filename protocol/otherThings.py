import struct
from protocol import MCField, VarInt

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
