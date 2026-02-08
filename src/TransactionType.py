import enum


class TransactionType(enum.Enum):
    ACK = 1
    DATA = 2
    RETRANSMIT = 3
    RELAY = 4