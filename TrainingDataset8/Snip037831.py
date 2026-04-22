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