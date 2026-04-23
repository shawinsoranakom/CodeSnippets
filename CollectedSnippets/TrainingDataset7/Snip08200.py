def memcache_key_warnings(key):
    if len(key) > MEMCACHE_MAX_KEY_LENGTH:
        yield (
            "Cache key will cause errors if used with memcached: %r "
            "(longer than %s)" % (key, MEMCACHE_MAX_KEY_LENGTH)
        )
    if memcached_error_chars_re.search(key):
        yield (
            "Cache key contains characters that will cause errors if used with "
            f"memcached: {key!r}"
        )