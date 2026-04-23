def _run_finalizers(minpriority=None):
    '''
    Run all finalizers whose exit priority is not None and at least minpriority

    Finalizers with highest priority are called first; finalizers with
    the same priority will be called in reverse order of creation.
    '''
    if _finalizer_registry is None:
        # This function may be called after this module's globals are
        # destroyed.  See the _exit_function function in this module for more
        # notes.
        return

    if minpriority is None:
        f = lambda p : p[0] is not None
    else:
        f = lambda p : p[0] is not None and p[0] >= minpriority

    # Careful: _finalizer_registry may be mutated while this function
    # is running (either by a GC run or by another thread).

    # list(_finalizer_registry) should be atomic, while
    # list(_finalizer_registry.items()) is not.
    keys = [key for key in list(_finalizer_registry) if f(key)]
    keys.sort(reverse=True)

    for key in keys:
        finalizer = _finalizer_registry.get(key)
        # key may have been removed from the registry
        if finalizer is not None:
            sub_debug('calling %s', finalizer)
            try:
                finalizer()
            except Exception:
                import traceback
                traceback.print_exc()

    if minpriority is None:
        _finalizer_registry.clear()