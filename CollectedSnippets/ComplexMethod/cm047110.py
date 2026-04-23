def _unquote_to_bytes(string: str | bytes, unsafe: str | bytes = "") -> bytes:
    if isinstance(string, str):
        string = string.encode("utf-8")

    if isinstance(unsafe, str):
        unsafe = unsafe.encode("utf-8")

    unsafe = frozenset(bytearray(unsafe))
    groups = iter(string.split(b"%"))
    result = bytearray(next(groups, b""))

    try:
        hex_to_byte = _unquote_maps[unsafe]
    except KeyError:
        hex_to_byte = _unquote_maps[unsafe] = {
            h: b for h, b in _hextobyte.items() if b not in unsafe
        }

    for group in groups:
        code = group[:2]

        if code in hex_to_byte:
            result.append(hex_to_byte[code])
            result.extend(group[2:])
        else:
            result.append(37)  # %
            result.extend(group)

    return bytes(result)