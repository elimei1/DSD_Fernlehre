from dataclasses import dataclass, field


@dataclass
class SentPacketElement:
    senderID: int
    sequenceNumber: int
    counter: int = field(compare=False)
    timestamp: float = field(compare=False)