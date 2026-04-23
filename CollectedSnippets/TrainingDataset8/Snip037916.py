def wrapped_func(*args, **kwargs):
        """This function wrapper will only call the underlying function in
        the case of a cache miss. Cached objects are stored in the cache/
        directory."""

        if not config.get_option("client.caching"):
            _LOGGER.debug("Purposefully skipping cache")
            return non_optional_func(*args, **kwargs)

        name = non_optional_func.__qualname__

        if len(args) == 0 and len(kwargs) == 0:
            message = "Running `%s()`." % name
        else:
            message = "Running `%s(...)`." % name

        def get_or_create_cached_value():
            nonlocal cache_key
            if cache_key is None:
                # Delay generating the cache key until the first call.
                # This way we can see values of globals, including functions
                # defined after this one.
                # If we generated the key earlier we would only hash those
                # globals by name, and miss changes in their code or value.
                cache_key = _hash_func(non_optional_func, hash_funcs)

            # First, get the cache that's attached to this function.
            # This cache's key is generated (above) from the function's code.
            mem_cache = _mem_caches.get_cache(cache_key, max_entries, ttl)

            # Next, calculate the key for the value we'll be searching for
            # within that cache. This key is generated from both the function's
            # code and the arguments that are passed into it. (Even though this
            # key is used to index into a per-function cache, it must be
            # globally unique, because it is *also* used for a global on-disk
            # cache that is *not* per-function.)
            value_hasher = hashlib.new("md5")

            if args:
                update_hash(
                    args,
                    hasher=value_hasher,
                    hash_funcs=hash_funcs,
                    hash_reason=HashReason.CACHING_FUNC_ARGS,
                    hash_source=non_optional_func,
                )

            if kwargs:
                update_hash(
                    kwargs,
                    hasher=value_hasher,
                    hash_funcs=hash_funcs,
                    hash_reason=HashReason.CACHING_FUNC_ARGS,
                    hash_source=non_optional_func,
                )

            value_key = value_hasher.hexdigest()

            # Avoid recomputing the body's hash by just appending the
            # previously-computed hash to the arg hash.
            value_key = "%s-%s" % (value_key, cache_key)

            _LOGGER.debug("Cache key: %s", value_key)

            try:
                return_value = _read_from_cache(
                    mem_cache=mem_cache,
                    key=value_key,
                    persist=persist,
                    allow_output_mutation=allow_output_mutation,
                    func_or_code=non_optional_func,
                    hash_funcs=hash_funcs,
                )
                _LOGGER.debug("Cache hit: %s", non_optional_func)

            except CacheKeyNotFoundError:
                _LOGGER.debug("Cache miss: %s", non_optional_func)

                with _calling_cached_function(non_optional_func):
                    if suppress_st_warning:
                        with suppress_cached_st_function_warning():
                            return_value = non_optional_func(*args, **kwargs)
                    else:
                        return_value = non_optional_func(*args, **kwargs)

                _write_to_cache(
                    mem_cache=mem_cache,
                    key=value_key,
                    value=return_value,
                    persist=persist,
                    allow_output_mutation=allow_output_mutation,
                    func_or_code=non_optional_func,
                    hash_funcs=hash_funcs,
                )

            return return_value

        if show_spinner:
            with spinner(message):
                return get_or_create_cached_value()
        else:
            return get_or_create_cached_value()