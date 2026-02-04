import struct


class Packet:
    # definition of struct
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
    HEADER_FORMAT = "!BIHB"
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT) # equals 8 Bytes

    # constant for the type
    ACK_TYPE = 0
    DATA_TYPE = 1

    def __init__(self, sender_id, sequence_number, is_ack, payload=b""):
        self.sender_id = sender_id
        self.sequence_number = sequence_number
        self.is_ack = is_ack
        
        # ensure, Payload are Bytes
        if isinstance(payload, str):
            self.payload = payload.encode('utf-8')
        else:
            self.payload = payload
            
        # Placeholder for checksum
        self.checksum = 0

    def to_bytes(self):
        """
        converts the objekt in a byte array (serialize)
        """
        # 1. convert Sender ID to Bytes
        # we need that to calc the lenght of the header 
        sid_bytes = str(self.sender_id).encode('utf-8')
        sid_len = len(sid_bytes)

        # security check: Does the ID fit 1Byte (max 255)
        if sid_len > 255:
            raise ValueError("Sender ID too long (max 255 bytes)")

        # 2. determine packet type (0 or 1)
        p_type = self.ACK_TYPE if self.is_ack else self.DATA_TYPE

        # 3. create header
        # structure: Type, SeqNum, Checksum, ID_Length
        header = struct.pack(self.HEADER_FORMAT, p_type, self.sequence_number, self.checksum, sid_len)

        # 4. return fully assembled packet
        return header + sid_bytes + self.payload

    @classmethod
    def from_bytes(cls, data_bytes):
        """
        Converts bytes back into a object (deserialization).
        """
        # 1. Check if enough data for header
        if len(data_bytes) < cls.HEADER_SIZE:
            raise ValueError("Packet too short (Header missing)")

        # 2. unpackt header (first 8 bytes)
        # unpack returns tuple: (Type, SeqNum, Checksum, ID_Len)
        header_values = struct.unpack(cls.HEADER_FORMAT, data_bytes[:cls.HEADER_SIZE])
        
        p_type = header_values[0]
        seq_num = header_values[1]
        received_checksum = header_values[2]
        sid_len = header_values[3]

        # 3. Check: if remaining data is enough for SenderID?
        if len(data_bytes) < cls.HEADER_SIZE + sid_len:
            raise ValueError("Packet too short (SenderID missing)")

        # 4. Slicing the transmitter ID and payload
        # ID start ist directly after header
        sid_start = cls.HEADER_SIZE
        sid_end = sid_start + sid_len
        
        # extract ID and decode
        sender_id = data_bytes[sid_start:sid_end].decode('utf-8')
        
        # rest after that is payload
        payload = data_bytes[sid_end:]

        # 5. create new object
        is_ack = (p_type == cls.ACK_TYPE)
        packet = cls(sender_id, seq_num, is_ack, payload)
        
        # important: set received checksum to validate it afterwards
        packet.checksum = received_checksum
        
        return packet

    @staticmethod
    def calculate_checksum(data_bytes):
        # HIER kommt im nächsten Schritt deine Magie rein.
        # Aktuell geben wir einfach 0 zurück.
        return 0