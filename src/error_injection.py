def inject_error(raw_data: bytes, bit_index: int) -> tuple[bytes, str]:
    # convert to bytearray
    data = bytearray(raw_data)
    
    # get affected byte
    byte_index = bit_index // 8
    
    # get affected bit in byte
    bit_within_byte = bit_index % 8
    
    if byte_index >= len(data):
        print(f"Index {bit_index} out of range. No error injected.")
        return raw_data, "Index out of range"

    # Bit toggle (XOR with mask)
    original_byte = data[byte_index]
    data[byte_index] ^= (1 << bit_within_byte)
    new_byte = data[byte_index]
    
    msg = f"Bit flip at index {bit_index} (Byte {byte_index}, Bit {bit_within_byte}): 0x{original_byte:02X} -> 0x{new_byte:02X}"
    return bytes(data), msg