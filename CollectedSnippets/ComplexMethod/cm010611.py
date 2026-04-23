def _lazy_init():
    global _initialized, _queued_calls
    if is_initialized() or hasattr(_tls, "is_initializing"):
        return
    with _initialization_lock:
        # We be double-checked locking, boys!  This is OK because
        # the above test was GIL protected anyway.  The inner test
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
                "Cannot re-initialize CUDA in forked subprocess. To use CUDA with "
                "multiprocessing, you must use the 'spawn' start method"
            )
        if not hasattr(torch._C, "_cuda_getDeviceCount"):
            raise AssertionError("Torch not compiled with CUDA enabled")
        if _cudart is None:
            raise AssertionError(
                "libcudart functions unavailable. It looks like you have a broken build?"
            )
        # This function throws if there's a driver initialization error, no GPUs
        # are found or any other error occurs
        torch._C._cuda_init()
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
                        f"CUDA call failed lazily at initialization with error: {str(e)}\n\n"
                        f"CUDA call was originally invoked at:\n\n{''.join(orig_traceback)}"
                    )
                    raise DeferredCudaCallError(msg) from e
        finally:
            delattr(_tls, "is_initializing")
        _initialized = True