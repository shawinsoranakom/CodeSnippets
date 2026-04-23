def ascii85_encode(data: bytes) -> bytes:
    
    binary_data = "".join(bin(ord(d))[2:].zfill(8) for d in data.decode("utf-8"))
    null_values = (32 * ((len(binary_data) // 32) + 1) - len(binary_data)) // 8
    binary_data = binary_data.ljust(32 * ((len(binary_data) // 32) + 1), "0")
    b85_chunks = [int(_s, 2) for _s in map("".join, zip(*[iter(binary_data)] * 32))]
    result = "".join(_base10_to_85(chunk)[::-1] for chunk in b85_chunks)
    return bytes(result[:-null_values] if null_values % 4 != 0 else result, "utf-8")
