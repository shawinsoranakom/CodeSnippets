def get_container_cursor(
    root_container: Optional[int],
) -> Optional["RunningCursor"]:
    """Return the top-level RunningCursor for the given container.
    This is the cursor that is used when user code calls something like
    `st.foo` (which uses the main container) or `st.sidebar.foo` (which uses
    the sidebar container).
    """
    if root_container is None:
        return None

    ctx = get_script_run_ctx()

    if ctx is None:
        return None

    if root_container in ctx.cursors:
        return ctx.cursors[root_container]

    cursor = RunningCursor(root_container=root_container)
    ctx.cursors[root_container] = cursor
    return cursor