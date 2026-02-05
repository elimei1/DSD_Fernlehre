def inject_error(raw_data: bytes, bit_index: int) -> bytes:
    """
    Toggles a single bit in the raw byte stream to simulate a transmission error.
    
    Args:
        raw_data: The original packet bytes received from the socket.
        bit_index: The global index of the bit to flip (0 to len*8 - 1).
    """
    # convert to bytearray
    data = bytearray(raw_data)
    
    # 1. get affected byte
    byte_index = bit_index // 8
    
    # 2. get affected bit in byte
    bit_within_byte = bit_index % 8
    
    if byte_index >= len(data):
        print(f"Index {bit_index} out of range. No error injected.")
        return raw_data

    # 3. Bit toggle (XOR with mask)
    # example: bit_within_byte = 3 -> mask = 00001000 (1 << 3)
    data[byte_index] ^= (1 << bit_within_byte)
    
    return bytes(data)