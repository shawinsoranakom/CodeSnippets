def _write_to_cache(
    mem_cache: MemCache,
    key: str,
    value: Any,
    persist: bool,
    allow_output_mutation: bool,
    func_or_code: Callable[..., Any],
    hash_funcs: Optional[HashFuncsDict] = None,
):
    _write_to_mem_cache(
        mem_cache, key, value, allow_output_mutation, func_or_code, hash_funcs
    )
    if persist:
        _write_to_disk_cache(key, value)