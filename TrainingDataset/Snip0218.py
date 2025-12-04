def base32_decode(data: bytes) -> bytes:

    binary_chunks = "".join(
        bin(B32_CHARSET.index(_d))[2:].zfill(5)
        for _d in data.decode("utf-8").strip("=")
    )
    binary_data = list(map("".join, zip(*[iter(binary_chunks)] * 8)))
    return bytes("".join([chr(int(_d, 2)) for _d in binary_data]), "utf-8")

