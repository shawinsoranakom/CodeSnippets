def base16_decode(data: str) -> bytes:
   
    if (len(data) % 2) != 0:
        raise ValueError(
            """Base16 encoded data is invalid:
Data does not have an even number of hex digits."""
        )
   
    if not set(data) <= set("0123456789ABCDEF"):
        raise ValueError(
            """Base16 encoded data is invalid:
Data is not uppercase hex or it contains invalid characters."""
        )
  
    return bytes(int(data[i] + data[i + 1], 16) for i in range(0, len(data), 2))
