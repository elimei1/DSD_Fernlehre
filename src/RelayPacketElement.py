from dataclasses import dataclass, field


@dataclass
class RelayPacketElement:
    senderID: int
    sequenceNumber: int
    timestamp: float = field(compare=False)