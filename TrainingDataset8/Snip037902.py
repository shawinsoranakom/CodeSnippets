def cache(
    func: Optional[F] = None,
    persist: bool = False,
    allow_output_mutation: bool = False,
    show_spinner: bool = True,
    suppress_st_warning: bool = False,
    hash_funcs: Optional[HashFuncsDict] = None,
    max_entries: Optional[int] = None,
    ttl: Optional[float] = None,
) -> Union[Callable[[F], F], F]:
    """Function decorator to memoize function executions.

    Parameters
    ----------
    func : callable
        The function to cache. Streamlit hashes the function and dependent code.

    persist : boolean
        Whether to persist the cache on disk.

    allow_output_mutation : boolean
        Streamlit shows a warning when return values are mutated, as that
        can have unintended consequences. This is done by hashing the return value internally.

        If you know what you're doing and would like to override this warning, set this to True.

    show_spinner : boolean
        Enable the spinner. Default is True to show a spinner when there is
        a cache miss.

    suppress_st_warning : boolean
        Suppress warnings about calling Streamlit commands from within
        the cached function.

    hash_funcs : dict or None
        Mapping of types or fully qualified names to hash functions. This is used to override
        the behavior of the hasher inside Streamlit's caching mechanism: when the hasher
        encounters an object, it will first check to see if its type matches a key in this
        dict and, if so, will use the provided function to generate a hash for it. See below
        for an example of how this can be used.

    max_entries : int or None
        The maximum number of entries to keep in the cache, or None
        for an unbounded cache. (When a new entry is added to a full cache,
        the oldest cached entry will be removed.) The default is None.

    ttl : float or None
        The maximum number of seconds to keep an entry in the cache, or
        None if cache entries should not expire. The default is None.

    Example
    -------
    >>> @st.cache
    ... def fetch_and_clean_data(url):
    ...     # Fetch data from URL here, and then clean it up.
    ...     return data
    ...
    >>> d1 = fetch_and_clean_data(DATA_URL_1)
    >>> # Actually executes the function, since this is the first time it was
    >>> # encountered.
    >>>
    >>> d2 = fetch_and_clean_data(DATA_URL_1)
    >>> # Does not execute the function. Instead, returns its previously computed
    >>> # value. This means that now the data in d1 is the same as in d2.
    >>>
    >>> d3 = fetch_and_clean_data(DATA_URL_2)
    >>> # This is a different URL, so the function executes.

    To set the ``persist`` parameter, use this command as follows:

    >>> @st.cache(persist=True)
    ... def fetch_and_clean_data(url):
    ...     # Fetch data from URL here, and then clean it up.
    ...     return data

    To disable hashing return values, set the ``allow_output_mutation`` parameter to ``True``:

    >>> @st.cache(allow_output_mutation=True)
    ... def fetch_and_clean_data(url):
    ...     # Fetch data from URL here, and then clean it up.
    ...     return data


    To override the default hashing behavior, pass a custom hash function.
    You can do that by mapping a type (e.g. ``MongoClient``) to a hash function (``id``) like this:

    >>> @st.cache(hash_funcs={MongoClient: id})
    ... def connect_to_database(url):
    ...     return MongoClient(url)

    Alternatively, you can map the type's fully-qualified name
    (e.g. ``"pymongo.mongo_client.MongoClient"``) to the hash function instead:

    >>> @st.cache(hash_funcs={"pymongo.mongo_client.MongoClient": id})
    ... def connect_to_database(url):
    ...     return MongoClient(url)

    """
    _LOGGER.debug("Entering st.cache: %s", func)

    # Support passing the params via function decorator, e.g.
    # @st.cache(persist=True, allow_output_mutation=True)
    if func is None:

        def wrapper(f: F) -> F:
            return cache(
                func=f,
                persist=persist,
                allow_output_mutation=allow_output_mutation,
                show_spinner=show_spinner,
                suppress_st_warning=suppress_st_warning,
                hash_funcs=hash_funcs,
                max_entries=max_entries,
                ttl=ttl,
            )

        return wrapper
    else:
        # To make mypy type narrow Optional[F] -> F
        non_optional_func = func

    cache_key = None

    @functools.wraps(non_optional_func)
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

    # Make this a well-behaved decorator by preserving important function
    # attributes.
    try:
        wrapped_func.__dict__.update(non_optional_func.__dict__)
    except AttributeError:
        # For normal functions this should never happen, but if so it's not problematic.
        pass

    return cast(F, wrapped_func)