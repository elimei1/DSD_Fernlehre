from dataclasses import dataclass

from packet import Packet


@dataclass
class Transaction:
    data: Packet
    timestamp: float
    retries: int
    destination: tuple[str, int]