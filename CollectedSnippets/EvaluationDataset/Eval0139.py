def parse_file(file_path: str) -> list[Letter]:

    chars: dict[str, int] = {}
    with open(file_path) as f:
        while True:
            c = f.read(1)
            if not c:
                break
            chars[c] = chars[c] + 1 if c in chars else 1
    return sorted((Letter(c, f) for c, f in chars.items()), key=lambda x: x.freq)
