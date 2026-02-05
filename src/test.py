import checksum as cs
from packet import Packet

def run_packet_integrity_test():
    print("=== Step 1: Create a new Data Packet ===")
    # Ein Paket mit Daten erstellen. Die Checksumme ist initial 0.
    p = (Packet()
         .setSenderID("Tristan")
         .setSequenceNumber(101)
         .setPayload("Hello Reliability!"))
    
    print(f"Original Packet: {p.getHeaderMap()}")

    print("\n=== Step 2: Calculate and Set Checksum ===")
    # 1. Paket als Bytes generieren (mit Checksumme = 0)
    raw_bytes_for_calculation = p.to_bytes()
    
    # 2. RFC 1071 Checksumme über diese Bytes berechnen
    calculated_checksum = cs.internet_checksum(raw_bytes_for_calculation)
    print(f"Calculated Checksum: {calculated_checksum} (Bin: {calculated_checksum:016b})")
    
    # 3. Checksumme im Objekt setzen
    p.setChecksum(calculated_checksum)
    
    # 4. Finales Paket generieren
    final_packet_bytes = p.to_bytes()
    print(f"Final Packet Length: {len(final_packet_bytes)} bytes")

    print("\n=== Step 3: Validate Correct Packet ===")
    # Validierung: Das Ergebnis muss 0 sein, wenn das Paket unverändert ist
    is_valid = cs.validate_checksum(final_packet_bytes)
    print(f"Is packet valid? {is_valid}")
    
    if not is_valid:
        print("FAILED: The correct packet should be valid!")
        return

    print("\n=== Step 4: Simulate Error Injection (Bit Flip) ===")
    # Wir nehmen die finalen Bytes und kippen ein Bit im Payload
    # Wir nehmen das allerletzte Byte (Index -1)
    corrupted_bytes = bytearray(final_packet_bytes)
    corrupted_bytes[-1] ^= 0b00000001 # Das letzte Bit kippen
    
    print(f"Original last byte:  {final_packet_bytes[-1]:08b}")
    print(f"Corrupted last byte: {corrupted_bytes[-1]:08b}")

    print("\n=== Step 5: Validate Corrupted Packet ===")
    # Validierung des kaputten Pakets
    is_valid_after_corruption = cs.validate_checksum(bytes(corrupted_bytes))
    print(f"Is corrupted packet valid? {is_valid_after_corruption}")
    
    if not is_valid_after_corruption:
        print("SUCCESS: The checksum correctly detected the bit error!")
    else:
        print("FAILED: The checksum did not detect the error!")

    print("\n=== Step 6: Test Deserialization (from_bytes) ===")
    # Testen, ob wir aus den Bytes wieder ein Packet-Objekt machen können
    p_received = Packet.from_bytes(final_packet_bytes)
    print(f"Received Sender: {p_received.sender_id}")
    print(f"Received Payload: {p_received.payload}")
    print(f"Received Checksum: {p_received.checksum}")

if __name__ == "__main__":
    run_packet_integrity_test()