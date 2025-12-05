import struct

class Packet:
    def __init__(self, sender_id, sequence_number, is_ack, payload=b""):
        # Initialisierung der Paketdaten
        self.sender_id = sender_id
        self.sequence_number = sequence_number
        self.is_ack = is_ack  # Boolean oder Integer Flag für ACK vs DATA
        self.payload = payload
        self.checksum = 0     # Wird später berechnet

    def to_bytes(self):
        """
        Wandelt das Paket-Objekt in ein Byte-Array (UDP-Datagramm-Payload) um.
        """
        # TODO: Verwende das 'struct' Modul, um den Header binär zu packen.
        # Empfohlenes Format: SenderID (int), SeqNum (int), Flags (int), Checksum (int).
        # Hänge anschließend den Payload an.
        # WICHTIG: Setze das Checksum-Feld vorerst auf 0 für die Berechnung.
        pass

    @staticmethod
    def calculate_checksum(data_bytes):
        """
        Implementiert die Internet Checksum gemäß RFC 1071[cite: 57].
        """
        # TODO: Iteriere in 16-Bit-Schritten durch data_bytes.
        # TODO: Addiere die Werte (Summe).
        # TODO: Handle Overflows (Carries), indem du sie wieder zur Summe addierst (Einerkomplement).
        # TODO: Invertiere das Ergebnis am Ende (Bitwise NOT: ~sum).
        # WICHTIG: Keine vorgefertigten Libraries verwenden[cite: 58].
        pass
    
    @classmethod
    def from_bytes(cls, data_bytes):
        """
        Erstellt ein Packet-Objekt aus empfangenen Bytes.
        """
        # TODO: Nutze 'struct.unpack', um den Header zu extrahieren.
        # TODO: Trenne Header und Payload.
        # TODO: Gib ein neues Packet-Objekt zurück.
        pass