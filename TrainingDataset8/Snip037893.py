def _read_from_mem_cache(
    mem_cache: MemCache,
    key: str,
    allow_output_mutation: bool,
    func_or_code: Callable[..., Any],
    hash_funcs: Optional[HashFuncsDict],
) -> Any:
    cache = mem_cache.cache
    if key in cache:
        entry = cache[key]

        if not allow_output_mutation:
            computed_output_hash = _get_output_hash(
                entry.value, func_or_code, hash_funcs
            )
            stored_output_hash = entry.hash

            if computed_output_hash != stored_output_hash:
                _LOGGER.debug("Cached object was mutated: %s", key)
                raise CachedObjectMutationError(entry.value, func_or_code)

        _LOGGER.debug("Memory cache HIT: %s", type(entry.value))
        return entry.value

    else:
        _LOGGER.debug("Memory cache MISS: %s", key)
        raise CacheKeyNotFoundError("Key not found in mem cache")