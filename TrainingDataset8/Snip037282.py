def on_config_parsed(
    func: Callable[[], None], force_connect=False, lock=False
) -> Callable[[], bool]:
    """Wait for the config file to be parsed then call func.

    If the config file has already been parsed, just calls func immediately
    unless force_connect is set.

    Parameters
    ----------
    func : Callable[[], None]
        A function to run on config parse.

    force_connect : bool
        Wait until the next config file parse to run func, even if config files
        have already been parsed.

    lock : bool
        If set, grab _config_lock before running func.

    Returns
    -------
    Callable[[], bool]
        A function that the caller can use to deregister func.
    """

    # We need to use the same receiver when we connect or disconnect on the
    # Signal. If we don't do this, then the registered receiver won't be released
    # leading to a memory leak because the Signal will keep a reference of the
    # callable argument. When the callable argument is an object method, then
    # the reference to that object won't be released.
    receiver = lambda _: func_with_lock()

    def disconnect():
        return _on_config_parsed.disconnect(receiver)

    def func_with_lock():
        if lock:
            with _config_lock:
                func()
        else:
            func()

    if force_connect or not _config_options:
        # weak=False so that we have control of when the on_config_parsed
        # callback is deregistered.
        _on_config_parsed.connect(receiver, weak=False)
    else:
        func_with_lock()

    return disconnect