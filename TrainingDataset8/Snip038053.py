def get_script_run_ctx() -> Optional[ScriptRunContext]:
    """
    Returns
    -------
    ScriptRunContext | None
        The current thread's ScriptRunContext, or None if it doesn't have one.

    """
    thread = threading.current_thread()
    ctx: Optional[ScriptRunContext] = getattr(
        thread, SCRIPT_RUN_CONTEXT_ATTR_NAME, None
    )
    if ctx is None and runtime.exists():
        # Only warn about a missing ScriptRunContext if we were started
        # via `streamlit run`. Otherwise, the user is likely running a
        # script "bare", and doesn't need to be warned about streamlit
        # bits that are irrelevant when not connected to a session.
        LOGGER.warning("Thread '%s': missing ScriptRunContext", thread.name)

    return ctx