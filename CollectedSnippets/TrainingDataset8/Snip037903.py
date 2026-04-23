def _hash_func(func: Callable[..., Any], hash_funcs: Optional[HashFuncsDict]) -> str:
    # Create the unique key for a function's cache. The cache will be retrieved
    # from inside the wrapped function.
    #
    # A naive implementation would involve simply creating the cache object
    # right in the wrapper, which in a normal Python script would be executed
    # only once. But in Streamlit, we reload all modules related to a user's
    # app when the app is re-run, which means that - among other things - all
    # function decorators in the app will be re-run, and so any decorator-local
    # objects will be recreated.
    #
    # Furthermore, our caches can be destroyed and recreated (in response to
    # cache clearing, for example), which means that retrieving the function's
    # cache in the decorator (so that the wrapped function can save a lookup)
    # is incorrect: the cache itself may be recreated between
    # decorator-evaluation time and decorated-function-execution time. So we
    # must retrieve the cache object *and* perform the cached-value lookup
    # inside the decorated function.
    func_hasher = hashlib.new("md5")

    # Include the function's __module__ and __qualname__ strings in the hash.
    # This means that two identical functions in different modules
    # will not share a hash; it also means that two identical *nested*
    # functions in the same module will not share a hash.
    # We do not pass `hash_funcs` here, because we don't want our function's
    # name to get an unexpected hash.
    update_hash(
        (func.__module__, func.__qualname__),
        hasher=func_hasher,
        hash_funcs=None,
        hash_reason=HashReason.CACHING_FUNC_BODY,
        hash_source=func,
    )

    # Include the function's body in the hash. We *do* pass hash_funcs here,
    # because this step will be hashing any objects referenced in the function
    # body.
    update_hash(
        func,
        hasher=func_hasher,
        hash_funcs=hash_funcs,
        hash_reason=HashReason.CACHING_FUNC_BODY,
        hash_source=func,
    )
    cache_key = func_hasher.hexdigest()
    _LOGGER.debug(
        "mem_cache key for %s.%s: %s", func.__module__, func.__qualname__, cache_key
    )
    return cache_key