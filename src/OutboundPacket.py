from dataclasses import dataclass

from packet import Packet


@dataclass
class OutboundPacket:
    data: Packet
    destination: tuple[str, int]