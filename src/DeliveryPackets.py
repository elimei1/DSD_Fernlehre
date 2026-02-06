from dataclasses import dataclass

from DeliveryPacketType import DeliveryPacketType
from packet import Packet

@dataclass
class DeliveryPacket:
    data: Packet | str
    type: DeliveryPacketType

