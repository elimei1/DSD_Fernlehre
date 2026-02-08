from dataclasses import dataclass
from packet import Packet
from TransactionType import TransactionType


@dataclass
class Transaction:
    packet: Packet
    transactionType: TransactionType

    destination: tuple[str, int] = tuple()
    timestamp: float = -1.0
    retries: int = -1