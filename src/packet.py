import struct
from dataclasses import dataclass
from typing import ClassVar, Union


@dataclass
class Packet:
    # definition of struct
    # B=unsigned char, I=unsigned int, H=unsigned short
    # ! = Network Endian, B=unsigned char, I=unsigned int, H=unsigned short

    """
        Represents a packet in the Reliable Group Communication protocol.

        Structure:
        [ Fixed Header (8 bytes) ] [ Variable Header (SenderID) ] [ Payload ]

        Fixed Header Format (!BIHB):
        - PacketType (1 byte, unsigned char): 0=ACK, 1=DATA
        - SequenceNumber (4 bytes, unsigned int)
        - Checksum (2 bytes, unsigned short): Covers the entire packet (Header + SenderID + Payload)
        - SenderID Length (1 byte, unsigned char): Length of the following SenderID in bytes

        Variable Header:
        - SenderID (Variable length, encoded as UTF-8 bytes): Not part of the fixed header struct.

        Payload:
        - Variable length bytes: The actual message content.
    """

    HEADER_FORMAT: ClassVar[str] = "!BIHB"
    HEADER_SIZE: ClassVar[int] = struct.calcsize(HEADER_FORMAT)
    ACK_TYPE: ClassVar[int] = 0
    DATA_TYPE: ClassVar[int] = 1

    sender_id: str = ""
    sequence_number: int = 0
    packetType: bool = -1
    payload: str = ""
    checksum: int = 0

    def isAck(self):
        self.packetType = self.ACK_TYPE
        return self

    def isData(self):
        self.packetType = self.DATA_TYPE
        return self

    def setSenderID(self, sender_id):
        self.sender_id = sender_id
        self.senderID_length = len(sender_id)
        return self

    def setSequenceNumber(self, sequence_number):
        self.sequence_number = sequence_number
        return self

    def setChecksum(self, checksum):
        self.checksum = checksum
        return self

    def setPayload(self, payload):
        if (isinstance(payload, bytes)):
            self.payload = payload.decode("utf-8")
        else:
            self.payload = payload
        return self

    def getHeaderMap(self):
        header = {"HeaderFormat": self.HEADER_FORMAT, "PacketType": self.packetType, "SequenceNumber": self.sequence_number, "Checksum": self.checksum,
                  "SenderID_length": self.senderID_length, "SenderID": self.sender_id}
        return header

    def to_bytes(self):
        """
        converts the object in a byte array (serialize)
        """
        # 1. convert Sender ID to Bytesj
        # we need that to calc the lenght of the header
        sid_bytes: bytes = str(self.sender_id).encode("utf-8")
        sid_len: int = len(sid_bytes)

        # security check: Does the ID fit 1Byte (max 255)
        if sid_len > 255:
            raise ValueError("Sender ID too long (max 255 bytes)")

        # 3. create header
        # structure: Type, SeqNum, Checksum, ID_Length
        header: bytes = struct.pack(
            self.HEADER_FORMAT, self.packetType, self.sequence_number, self.checksum, sid_len
        )

        # 4. return fully assembled packet
        return header + sid_bytes + self.payload

    @classmethod
    def from_bytes(cls, data_bytes):
        """
        Converts bytes back into an object (deserialization).
        """
        # 1. Check if enough data for header
        if len(data_bytes) < cls.HEADER_SIZE:
            raise ValueError("Packet too short (Header missing)")

        # 2. unpackt header (first 8 bytes)
        # unpack returns tuple: (Type, SeqNum, Checksum, ID_Len)
        header_values = struct.unpack(cls.HEADER_FORMAT, data_bytes[: cls.HEADER_SIZE])

        p_type = header_values[0]
        seq_num: int = header_values[1]
        received_checksum = header_values[2]
        sid_len: int = header_values[3]

        # 3. Check: if remaining data is enough for SenderID?
        if len(data_bytes) < cls.HEADER_SIZE + sid_len:
            raise ValueError("Packet too short (SenderID missing)")

        # 4. Slicing the transmitter ID and payload
        # ID start is directly after header
        sid_start: int = cls.HEADER_SIZE
        sid_end: int = sid_start + sid_len
        sender_id: str = data_bytes[sid_start:sid_end].decode("utf-8")

        # 5. create new object
        packet = Packet().setPayload(data_bytes[sid_end:]).setChecksum(received_checksum).setSenderID(sender_id).setSequenceNumber(seq_num)
        is_ack = (p_type == cls.ACK_TYPE)
        packet.isAck() if (p_type == cls.ACK_TYPE) else packet.isData()

        return packet

    @staticmethod
    def calculate_checksum(data_bytes):

        return 0
