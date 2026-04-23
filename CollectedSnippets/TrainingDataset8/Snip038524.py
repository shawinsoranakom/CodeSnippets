def _serialize_bytes_arg(key: str, value: Any) -> SpecialArg:
    special_arg = SpecialArg()
    special_arg.key = key
    special_arg.bytes = to_bytes(value)
    return special_arg