def _get_output_hash(
    value: Any, func_or_code: Callable[..., Any], hash_funcs: Optional[HashFuncsDict]
) -> bytes:
    hasher = hashlib.new("md5")
    update_hash(
        value,
        hasher=hasher,
        hash_funcs=hash_funcs,
        hash_reason=HashReason.CACHING_FUNC_OUTPUT,
        hash_source=func_or_code,
    )
    return hasher.digest()