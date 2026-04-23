def base64_encode(data: bytes) -> bytes:
    
    if not isinstance(data, bytes):
        msg = f"a bytes-like object is required, not '{data.__class__.__name__}'"
        raise TypeError(msg)

    binary_stream = "".join(bin(byte)[2:].zfill(8) for byte in data)

    padding_needed = len(binary_stream) % 6 != 0

    if padding_needed:
        padding = b"=" * ((6 - len(binary_stream) % 6) // 2)

       
        binary_stream += "0" * (6 - len(binary_stream) % 6)
    else:
        padding = b""

    return (
        "".join(
            B64_CHARSET[int(binary_stream[index : index + 6], 2)]
            for index in range(0, len(binary_stream), 6)
        ).encode()
        + padding
    )
