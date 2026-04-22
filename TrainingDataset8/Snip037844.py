def __call__(
        self,
        func: Optional[F] = None,
        *,
        show_spinner: Union[bool, str] = True,
        suppress_st_warning=False,
        experimental_allow_widgets: bool = False,
    ):
        """Function decorator to store singleton objects.

        Each singleton object is shared across all users connected to the app.
        Singleton objects *must* be thread-safe, because they can be accessed from
        multiple threads concurrently.

        (If thread-safety is an issue, consider using ``st.session_state`` to
        store per-session singleton objects instead.)

        You can clear a memoized function's cache with f.clear().

        Parameters
        ----------
        func : callable
            The function that creates the singleton. Streamlit hashes the
            function's source code.

        show_spinner : boolean or string
            Enable the spinner. Default is True to show a spinner when there is
            a "cache miss" and the singleton is being created. If string,
            value of show_spinner param will be used for spinner text.

        suppress_st_warning : boolean
            Suppress warnings about calling Streamlit commands from within
            the singleton function.

        experimental_allow_widgets : boolean
            Allow widgets to be used in the singleton function. Defaults to False.

        .. note::
            Support for widgets in cached functions is currently experimental.
            To enable it, set the parameter ``experimental_allow_widgets=True``
            in ``@st.experimental_singleton``. Note that this may lead to excessive
            memory use since the widget value is treated as an additional input
            parameter to the cache. We may remove support for this option at any
            time without notice.

        Example
        -------
        >>> @st.experimental_singleton
        ... def get_database_session(url):
        ...     # Create a database session object that points to the URL.
        ...     return session
        ...
        >>> s1 = get_database_session(SESSION_URL_1)
        >>> # Actually executes the function, since this is the first time it was
        >>> # encountered.
        >>>
        >>> s2 = get_database_session(SESSION_URL_1)
        >>> # Does not execute the function. Instead, returns its previously computed
        >>> # value. This means that now the connection object in s1 is the same as in s2.
        >>>
        >>> s3 = get_database_session(SESSION_URL_2)
        >>> # This is a different URL, so the function executes.

        By default, all parameters to a singleton function must be hashable.
        Any parameter whose name begins with ``_`` will not be hashed. You can use
        this as an "escape hatch" for parameters that are not hashable:

        >>> @st.experimental_singleton
        ... def get_database_session(_sessionmaker, url):
        ...     # Create a database connection object that points to the URL.
        ...     return connection
        ...
        >>> s1 = get_database_session(create_sessionmaker(), DATA_URL_1)
        >>> # Actually executes the function, since this is the first time it was
        >>> # encountered.
        >>>
        >>> s2 = get_database_session(create_sessionmaker(), DATA_URL_1)
        >>> # Does not execute the function. Instead, returns its previously computed
        >>> # value - even though the _sessionmaker parameter was different
        >>> # in both calls.

        A singleton function's cache can be procedurally cleared:

        >>> @st.experimental_singleton
        ... def get_database_session(_sessionmaker, url):
        ...     # Create a database connection object that points to the URL.
        ...     return connection
        ...
        >>> get_database_session.clear()
        >>> # Clear all cached entries for this function.

        """
        # Support passing the params via function decorator, e.g.
        # @st.singleton(show_spinner=False)
        if func is None:
            return lambda f: create_cache_wrapper(
                SingletonFunction(
                    func=f,
                    show_spinner=show_spinner,
                    suppress_st_warning=suppress_st_warning,
                    allow_widgets=experimental_allow_widgets,
                )
            )

        return create_cache_wrapper(
            SingletonFunction(
                func=cast(types.FunctionType, func),
                show_spinner=show_spinner,
                suppress_st_warning=suppress_st_warning,
                allow_widgets=experimental_allow_widgets,
            )
        )