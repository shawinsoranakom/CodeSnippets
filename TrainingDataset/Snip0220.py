def base64_decode(encoded_data: str) -> bytes:

    if not isinstance(encoded_data, bytes) and not isinstance(encoded_data, str):
        msg = (
            "argument should be a bytes-like object or ASCII string, "
            f"not '{encoded_data.__class__.__name__}'"
        )
        raise TypeError(msg)

    if isinstance(encoded_data, bytes):
        try:
            encoded_data = encoded_data.decode("utf-8")
        except UnicodeDecodeError:
            raise ValueError("base64 encoded data should only contain ASCII characters")

    padding = encoded_data.count("=")

    if padding:
        assert all(char in B64_CHARSET for char in encoded_data[:-padding]), (
            "Invalid base64 character(s) found."
        )
    else:
        assert all(char in B64_CHARSET for char in encoded_data), (
            "Invalid base64 character(s) found."
        )

    assert len(encoded_data) % 4 == 0 and padding < 3, "Incorrect padding"

    if padding:

      encoded_data = encoded_data[:-padding]

        binary_stream = "".join(
            bin(B64_CHARSET.index(char))[2:].zfill(6) for char in encoded_data
        )[: -padding * 2]
    else:
        binary_stream = "".join(
            bin(B64_CHARSET.index(char))[2:].zfill(6) for char in encoded_data
        )

    data = [
        int(binary_stream[index : index + 8], 2)
        for index in range(0, len(binary_stream), 8)
    ]

    return bytes(data)
