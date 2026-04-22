def __call__(
        self,
        func: Optional[F] = None,
        *,
        persist: Optional[str] = None,
        show_spinner: Union[bool, str] = True,
        suppress_st_warning: bool = False,
        max_entries: Optional[int] = None,
        ttl: Optional[Union[float, timedelta]] = None,
        experimental_allow_widgets: bool = False,
    ):
        """Function decorator to memoize function executions.

        Memoized data is stored in "pickled" form, which means that the return
        value of a memoized function must be pickleable.

        Each caller of a memoized function gets its own copy of the cached data.

        You can clear a memoized function's cache with f.clear().

        Parameters
        ----------
        func : callable
            The function to memoize. Streamlit hashes the function's source code.

        persist : str or None
            Optional location to persist cached data to. Currently, the only
            valid value is "disk", which will persist to the local disk.

        show_spinner : boolean
            Enable the spinner. Default is True to show a spinner when there is
            a cache miss.

        suppress_st_warning : boolean
            Suppress warnings about calling Streamlit commands from within
            the cached function.

        max_entries : int or None
            The maximum number of entries to keep in the cache, or None
            for an unbounded cache. (When a new entry is added to a full cache,
            the oldest cached entry will be removed.) The default is None.

        ttl : float or timedelta or None
            The maximum number of seconds to keep an entry in the cache, or
            None if cache entries should not expire. The default is None.
            Note that ttl is incompatible with `persist="disk"` - `ttl` will be
            ignored if `persist` is specified.

        experimental_allow_widgets : boolean
            Allow widgets to be used in the memoized function. Defaults to False.

        .. note::
            Support for widgets in cached functions is currently experimental.
            To enable it, set the parameter ``experimental_allow_widgets=True``
            in ``@st.experimental_memo``. Note that this may lead to excessive memory
            use since the widget value is treated as an additional input parameter
            to the cache. We may remove support for this option at any time without notice.

        Example
        -------
        >>> @st.experimental_memo
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

        >>> @st.experimental_memo(persist="disk")
        ... def fetch_and_clean_data(url):
        ...     # Fetch data from URL here, and then clean it up.
        ...     return data

        By default, all parameters to a memoized function must be hashable.
        Any parameter whose name begins with ``_`` will not be hashed. You can use
        this as an "escape hatch" for parameters that are not hashable:

        >>> @st.experimental_memo
        ... def fetch_and_clean_data(_db_connection, num_rows):
        ...     # Fetch data from _db_connection here, and then clean it up.
        ...     return data
        ...
        >>> connection = make_database_connection()
        >>> d1 = fetch_and_clean_data(connection, num_rows=10)
        >>> # Actually executes the function, since this is the first time it was
        >>> # encountered.
        >>>
        >>> another_connection = make_database_connection()
        >>> d2 = fetch_and_clean_data(another_connection, num_rows=10)
        >>> # Does not execute the function. Instead, returns its previously computed
        >>> # value - even though the _database_connection parameter was different
        >>> # in both calls.

        A memoized function's cache can be procedurally cleared:

        >>> @st.experimental_memo
        ... def fetch_and_clean_data(_db_connection, num_rows):
        ...     # Fetch data from _db_connection here, and then clean it up.
        ...     return data
        ...
        >>> fetch_and_clean_data.clear()
        >>> # Clear all cached entries for this function.

        """

        if persist not in (None, "disk"):
            # We'll eventually have more persist options.
            raise StreamlitAPIException(
                f"Unsupported persist option '{persist}'. Valid values are 'disk' or None."
            )

        ttl_seconds: Optional[float]

        if isinstance(ttl, timedelta):
            ttl_seconds = ttl.total_seconds()
        else:
            ttl_seconds = ttl

        def wrapper(f):
            # We use wrapper function here instead of lambda function to be able to log
            # warning in case both persist="disk" and ttl parameters specified
            if persist == "disk" and ttl is not None:
                _LOGGER.warning(
                    f"The memoized function '{f.__name__}' has a TTL that will be "
                    f"ignored. Persistent memo caches currently don't support TTL."
                )
            return create_cache_wrapper(
                MemoizedFunction(
                    func=f,
                    persist=persist,
                    show_spinner=show_spinner,
                    suppress_st_warning=suppress_st_warning,
                    max_entries=max_entries,
                    ttl=ttl_seconds,
                    allow_widgets=experimental_allow_widgets,
                )
            )

        # Support passing the params via function decorator, e.g.
        # @st.memo(persist=True, show_spinner=False)
        if func is None:
            return wrapper

        return create_cache_wrapper(
            MemoizedFunction(
                func=cast(types.FunctionType, func),
                persist=persist,
                show_spinner=show_spinner,
                suppress_st_warning=suppress_st_warning,
                max_entries=max_entries,
                ttl=ttl_seconds,
                allow_widgets=experimental_allow_widgets,
            )
        )