def _read_from_cache(
    mem_cache: MemCache,
    key: str,
    persist: bool,
    allow_output_mutation: bool,
    func_or_code: Callable[..., Any],
    hash_funcs: Optional[HashFuncsDict] = None,
) -> Any:
    """Read a value from the cache.

    Our goal is to read from memory if possible. If the data was mutated (hash
    changed), we show a warning. If reading from memory fails, we either read
    from disk or rerun the code.
    """
    try:
        return _read_from_mem_cache(
            mem_cache, key, allow_output_mutation, func_or_code, hash_funcs
        )

    except CachedObjectMutationError as e:
        handle_uncaught_app_exception(CachedObjectMutationWarning(e))
        return e.cached_value

    except CacheKeyNotFoundError as e:
        if persist:
            value = _read_from_disk_cache(key)
            _write_to_mem_cache(
                mem_cache, key, value, allow_output_mutation, func_or_code, hash_funcs
            )
            return value
        raise e