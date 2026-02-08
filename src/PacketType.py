import enum


class PacketType(enum.Enum):
    NONE = -1
    ACK = 0
    DATA = 1
