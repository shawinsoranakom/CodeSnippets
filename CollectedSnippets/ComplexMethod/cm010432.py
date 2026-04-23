def _lazy_init() -> None:
    global _initialized, _queued_calls
    if is_initialized() or hasattr(_tls, "is_initializing"):
        return
    with _initialization_lock:
        # We be double-checking locking, boys! This is OK because
        # the above test was GIL protected anyway. The inner test
        # is for when a thread blocked on some other thread which was
        # doing the initialization; when they get the lock, they will
        # find there is nothing left to do.
        if is_initialized():
            return
        # It is important to prevent other threads from entering _lazy_init
        # immediately, while we are still guaranteed to have the GIL, because some
        # of the C calls we make below will release the GIL
        if _is_in_bad_fork():
            raise RuntimeError(
                "Cannot re-initialize MTIA in forked subprocess. To use MTIA with "
                "multiprocessing, you must use the 'spawn' start method"
            )
        if not _is_compiled():
            raise AssertionError(
                "Torch not compiled with MTIA enabled. "
                "Ensure you have `import mtia.host_runtime.torch_mtia.dynamic_library` in your python "
                "src file and include `//mtia/host_runtime/torch_mtia:torch_mtia` as "
                "your target dependency!"
            )

        # Install the C++ resource manager to enable Buck resource lookup from Python.
        # This must be called before _mtia_init() which may access Buck resources.
        if is_fbcode() and is_prod():
            try:
                from libfb.py.cxx_resources import cxx_resource_manager

                cxx_resource_manager.install()
            except ModuleNotFoundError:
                # cxx_resource_manager is not available in all build configurations
                pass

        torch._C._mtia_init()
        # Some of the queued calls may reentrantly call _lazy_init();
        # we need to just return without initializing in that case.
        # However, we must not let any *other* threads in!
        _tls.is_initializing = True

        _queued_calls.extend(calls for calls in _lazy_seed_tracker.get_calls() if calls)

        try:
            for queued_call, orig_traceback in _queued_calls:
                try:
                    queued_call()
                except Exception as e:
                    msg = (
                        f"MTIA call failed lazily at initialization with error: {str(e)}\n\n"
                        f"MTIA call was originally invoked at:\n\n{''.join(orig_traceback)}"
                    )
                    raise DeferredMtiaCallError(msg) from e
        finally:
            delattr(_tls, "is_initializing")
        _initialized = True