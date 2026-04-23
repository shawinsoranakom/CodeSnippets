def base32_encode(data: bytes) -> bytes:
    
    binary_data = "".join(bin(ord(d))[2:].zfill(8) for d in data.decode("utf-8"))
    binary_data = binary_data.ljust(5 * ((len(binary_data) // 5) + 1), "0")
    b32_chunks = map("".join, zip(*[iter(binary_data)] * 5))
    b32_result = "".join(B32_CHARSET[int(chunk, 2)] for chunk in b32_chunks)
    return bytes(b32_result.ljust(8 * ((len(b32_result) // 8) + 1), "="), "utf-8")
