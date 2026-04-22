def add_script_run_ctx(
    thread: Optional[threading.Thread] = None, ctx: Optional[ScriptRunContext] = None
):
    """Adds the current ScriptRunContext to a newly-created thread.

    This should be called from this thread's parent thread,
    before the new thread starts.

    Parameters
    ----------
    thread : threading.Thread
        The thread to attach the current ScriptRunContext to.
    ctx : ScriptRunContext or None
        The ScriptRunContext to add, or None to use the current thread's
        ScriptRunContext.

    Returns
    -------
    threading.Thread
        The same thread that was passed in, for chaining.

    """
    if thread is None:
        thread = threading.current_thread()
    if ctx is None:
        ctx = get_script_run_ctx()
    if ctx is not None:
        setattr(thread, SCRIPT_RUN_CONTEXT_ATTR_NAME, ctx)
    return thread