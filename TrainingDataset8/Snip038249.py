def is_bytes_like(obj: object) -> TypeGuard[BytesLike]:
    """True if the type is considered bytes-like for the purposes of
    protobuf data marshalling."""
    return isinstance(obj, _BYTES_LIKE_TYPES)