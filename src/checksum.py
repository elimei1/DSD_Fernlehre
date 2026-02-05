def internet_checksum(data: bytes) -> int:
    if len(data) % 2 == 1:
        data += b"\x00"

    total_sum = 0
    for i in range(0, len(data), 2):
        word = (data[i] << 8) + data[i + 1]
        total_sum += word
        while total_sum >> 16:
            total_sum = (total_sum & 0xFFFF) + (total_sum >> 16)

    return (~total_sum) & 0xFFFF
