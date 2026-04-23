def _combine(
    poly: int,
    size_bits: int,
    init_crc: int,
    rev: bool,
    xor_out: int,
    crc1: int,
    crc2: int,
    len2: int,
) -> bytes:
    if len2 == 0:
        return _encode_to_bytes(crc1, size_bits)

    even = [0] * size_bits
    odd = [0] * size_bits

    crc1 ^= init_crc ^ xor_out

    if rev:
        # put operator for one zero bit in odd
        odd[0] = poly  # CRC-64 polynomial
        row = 1
        for n in range(1, size_bits):
            odd[n] = row
            row <<= 1
    else:
        row = 2
        for n in range(0, size_bits - 1):
            odd[n] = row
            row <<= 1
        odd[size_bits - 1] = poly

    gf2_matrix_square(even, odd)

    gf2_matrix_square(odd, even)

    while True:
        gf2_matrix_square(even, odd)
        if len2 & 1:
            crc1 = gf2_matrix_times(even, crc1)
        len2 >>= 1
        if len2 == 0:
            break

        gf2_matrix_square(odd, even)
        if len2 & 1:
            crc1 = gf2_matrix_times(odd, crc1)
        len2 >>= 1

        if len2 == 0:
            break

    crc1 ^= crc2

    return _encode_to_bytes(crc1, size_bits)