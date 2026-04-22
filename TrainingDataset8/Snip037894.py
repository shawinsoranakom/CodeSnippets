def _write_to_mem_cache(
    mem_cache: MemCache,
    key: str,
    value: Any,
    allow_output_mutation: bool,
    func_or_code: Callable[..., Any],
    hash_funcs: Optional[HashFuncsDict],
) -> None:
    if allow_output_mutation:
        hash = None
    else:
        hash = _get_output_hash(value, func_or_code, hash_funcs)

    mem_cache.display_name = f"{func_or_code.__module__}.{func_or_code.__qualname__}"
    mem_cache.cache[key] = _CacheEntry(value=value, hash=hash)