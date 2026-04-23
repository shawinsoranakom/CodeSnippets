def _lazy_init() -> None:
    global _initialized, _queued_calls
    if is_initialized() or hasattr(_tls, "is_initializing"):
        return
    with _initialization_lock:
        # This test was was protected via GIL. Double-check whether XPU has
        # already been initialized.
        if is_initialized():
            return
        # Stop promptly upon encountering a bad fork error.
        if _is_in_bad_fork():
            raise RuntimeError(
                "Cannot re-initialize XPU in forked subprocess. To use XPU with "
                "multiprocessing, you must use the 'spawn' start method"
            )
        if not _is_compiled():
            raise AssertionError("Torch not compiled with XPU enabled")
        # This function inits XPU backend and detects bad fork processing.
        torch._C._xpu_init()
        # Some of the queued calls may reentrantly call _lazy_init(); We need to
        # just return without initializing in that case.
        _tls.is_initializing = True

        _queued_calls.extend(calls for calls in _lazy_seed_tracker.get_calls() if calls)

        try:
            for queued_call, orig_traceback in _queued_calls:
                try:
                    queued_call()
                except Exception as e:
                    msg = (
                        f"XPU call failed lazily at initialization with error: {str(e)}\n\n"
                        f"XPU call was originally invoked at:\n\n{''.join(orig_traceback)}"
                    )
                    raise Exception(msg) from e  # noqa: TRY002
        finally:
            delattr(_tls, "is_initializing")
        _initialized = True