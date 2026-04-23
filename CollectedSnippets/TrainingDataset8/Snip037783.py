def update_hash(val: Any, hasher, cache_type: CacheType) -> None:
    """Updates a hashlib hasher with the hash of val.

    This is the main entrypoint to hashing.py.
    """
    ch = _CacheFuncHasher(cache_type)
    ch.update(hasher, val)