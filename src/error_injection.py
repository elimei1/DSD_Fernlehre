def inject_error(raw_data: bytes, bit_index: int) -> bytes:
    # convert to bytearray
    data = bytearray(raw_data)
    
    # get affected byte
    byte_index = bit_index // 8
    
    # get affected bit in byte
    bit_within_byte = bit_index % 8
    
    if byte_index >= len(data):
        print(f"Index {bit_index} out of range. No error injected.")
        return raw_data

    # Bit toggle (XOR with mask)
    data[byte_index] ^= (1 << bit_within_byte)
    
    return bytes(data)