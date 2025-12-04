def ascii85_decode(data: bytes) -> bytes:
    
    null_values = 5 * ((len(data) // 5) + 1) - len(data)
    binary_data = data.decode("utf-8") + "u" * null_values
    b85_chunks = map("".join, zip(*[iter(binary_data)] * 5))
    b85_segments = [[ord(_s) - 33 for _s in chunk] for chunk in b85_chunks]
    results = [bin(_base85_to_10(chunk))[2::].zfill(32) for chunk in b85_segments]
    char_chunks = [
        [chr(int(_s, 2)) for _s in map("".join, zip(*[iter(r)] * 8))] for r in results
    ]
    result = "".join("".join(char) for char in char_chunks)
    offset = int(null_values % 5 == 0)
    return bytes(result[: offset - null_values], "utf-8")
