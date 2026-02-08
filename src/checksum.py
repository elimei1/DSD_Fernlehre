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


def validate_checksum(raw_data: bytes) -> bool:
    if len(raw_data) < 8:
        return False

    # extract the received checksum from the header (index 5 & 6)
    received_checksum = (raw_data[5] << 8) + raw_data[6]

    # create a copy of the data where the checksum is 0
    mutable_data = bytearray(raw_data)
    mutable_data[5] = 0
    mutable_data[6] = 0

    # recalc checksum
    recalculated = internet_checksum(bytes(mutable_data))

    return received_checksum == recalculated
