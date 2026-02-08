import struct
from dataclasses import dataclass
from typing import ClassVar
import checksum as cs
from PacketType import PacketType


@dataclass
class Packet:
    # B=unsigned char, I=unsigned int, H=unsigned short
    # ! = Network Endian, B=unsigned char, I=unsigned int, H=unsigned short

    # [ Fixed Header (8 bytes) ] [ Variable Header (SenderID) ] [ Payload ]

    # Fixed Header Format (!BIHB):
    #    - PacketType (1 byte, unsigned char): 0=ACK, 1=DATA
    #    - SequenceNumber (4 bytes, unsigned int)
    #    - Checksum (2 bytes, unsigned short): Covers the entire packet (Header + SenderID + Payload)
    #    - SenderID Length (1 byte, unsigned char): Length of the following SenderID in bytes

    #    Variable Header:
    #    - SenderID (Variable length, encoded as UTF-8 bytes): Not part of the fixed header struct.

    #    Payload:
    #    - Variable length bytes: The actual message content.

    HEADER_FORMAT: ClassVar[str] = "!BIHB"
    HEADER_SIZE: ClassVar[int] = struct.calcsize(HEADER_FORMAT)

    sender_id: str = ""
    senderID_length: int = -1
    sequence_number: int = 0
    packetType: PacketType = PacketType.NONE
    payload: str = ""
    checksum: int = 0

    def setAck(self):
        self.packetType = PacketType.ACK
        return self

    def setSenderID(self, sender_id):
        # set sender id
        if isinstance(sender_id, bytes):
            self.sender_id = sender_id.decode("utf-8")
        else:
            self.sender_id = str(sender_id)

        # set senderId length
        if len(self.sender_id) > 255:
            raise ValueError("Sender ID too long (max 255 bytes)")
        self.senderID_length = len(self.sender_id)
        return self

    def setSequenceNumber(self, sequence_number):
        self.sequence_number = sequence_number
        return self

    def setChecksum(self, checksum):
        self.checksum = checksum
        return self

    def setPayload(self, payload):
        if isinstance(payload, bytes):
            self.payload = payload.decode("utf-8")
        else:
            self.payload = payload

        self.packetType = PacketType.DATA
        return self

    def getHeaderMap(self):
        return {"HeaderFormat": self.HEADER_FORMAT, "PacketType": self.packetType.value, "SequenceNumber": self.sequence_number, "Checksum": self.checksum,
                  "SenderID_length": self.senderID_length, "SenderID": self.sender_id}

    def getHeaderStruct(self):
        return struct.pack(
            self.HEADER_FORMAT,
            self.packetType.value,
            self.sequence_number,
            self.checksum,
            self.senderID_length,
        )

    def getPacketType(self):
        return self.packetType

    def isData(self):
        return self.packetType == PacketType.DATA

    def isAck(self):
        return self.packetType == PacketType.ACK

    def getSequenceNumber(self):
        return self.sequence_number

    def to_bytes(self):        
        sid_bytes = self.sender_id.encode('utf-8')
        # check that payload is bytes
        p_bytes = self.payload.encode('utf-8') if isinstance(self.payload, str) else self.payload

        self.checksum = 0
        
        # temp paket (header with checksum 0 + remainer)
        temp_header = self.getHeaderStruct()
        temp_packet = temp_header + sid_bytes + p_bytes
        
        # calc checksum an store in object
        self.checksum = cs.internet_checksum(temp_packet)
        
        return self.getHeaderStruct() + sid_bytes + p_bytes

    @classmethod
    def from_bytes(cls, data_bytes):
        # Check if enough data for header
        if len(data_bytes) < cls.HEADER_SIZE:
            raise ValueError("Packet too short (Header missing)")

        # unpackt header (first 8 bytes)
        header_values = struct.unpack(cls.HEADER_FORMAT, data_bytes[: cls.HEADER_SIZE])

        p_type = PacketType(header_values[0])
        seq_num: int = header_values[1]
        received_checksum = header_values[2]
        sid_len: int = header_values[3]

        # Check if remaining data is enough for SenderID?
        if len(data_bytes) < cls.HEADER_SIZE + sid_len:
            raise ValueError("Packet too short (SenderID missing)")

        # Slicing the transmitter ID and payload
        sid_start: int = cls.HEADER_SIZE
        sid_end: int = sid_start + sid_len

        # create new object
        packet = Packet().setChecksum(received_checksum).setSenderID(data_bytes[sid_start:sid_end]).setSequenceNumber(seq_num)
        if p_type == PacketType.ACK:
            packet.setAck()
        elif p_type == PacketType.DATA:
            packet.setPayload(data_bytes[sid_end:])

        return packet

