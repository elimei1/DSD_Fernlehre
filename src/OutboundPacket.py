from dataclasses import dataclass

from src.packet import Packet


@dataclass
class OutboundPacket:
    data: Packet
    destination: tuple[str, int]