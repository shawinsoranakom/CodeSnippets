def swap_odd_even_bits(num: int) -> int:

    even_bits = num & 0xAAAAAAAA

    odd_bits = num & 0x55555555

    return even_bits >> 1 | odd_bits << 1
