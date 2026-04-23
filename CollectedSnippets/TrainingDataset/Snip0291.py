def read_key_file(key_filename: str) -> tuple[int, int, int]:
    with open(key_filename) as fo:
        content = fo.read()
    key_size, n, eor_d = content.split(",")
    return (int(key_size), int(n), int(eor_d))
