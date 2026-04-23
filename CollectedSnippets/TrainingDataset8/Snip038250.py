def to_bytes(obj: BytesLike) -> bytes:
    """Converts the given object to bytes.

    Only types for which `is_bytes_like` is true can be converted; anything
    else will result in an exception.
    """
    if isinstance(obj, bytearray):
        return bytes(obj)
    elif isinstance(obj, bytes):
        return obj

    raise RuntimeError(f"{obj} is not convertible to bytes")