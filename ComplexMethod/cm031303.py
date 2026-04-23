def capture_call_graph(
    future: futures.Future | None = None,
    /,
    *,
    depth: int = 1,
    limit: int | None = None,
) -> FutureCallGraph | None:
    """Capture the async call graph for the current task or the provided Future.

    The graph is represented with three data structures:

    * FutureCallGraph(future, call_stack, awaited_by)

      Where 'future' is an instance of asyncio.Future or asyncio.Task.

      'call_stack' is a tuple of FrameGraphEntry objects.

      'awaited_by' is a tuple of FutureCallGraph objects.

    * FrameCallGraphEntry(frame)

      Where 'frame' is a frame object of a regular Python function
      in the call stack.

    Receives an optional 'future' argument. If not passed,
    the current task will be used. If there's no current task, the function
    returns None.

    If "capture_call_graph()" is introspecting *the current task*, the
    optional keyword-only 'depth' argument can be used to skip the specified
    number of frames from top of the stack.

    If the optional keyword-only 'limit' argument is provided, each call stack
    in the resulting graph is truncated to include at most ``abs(limit)``
    entries. If 'limit' is positive, the entries left are the closest to
    the invocation point. If 'limit' is negative, the topmost entries are
    left. If 'limit' is omitted or None, all entries are present.
    If 'limit' is 0, the call stack is not captured at all, only
    "awaited by" information is present.
    """

    loop = events._get_running_loop()

    if future is not None:
        # Check if we're in a context of a running event loop;
        # if yes - check if the passed future is the currently
        # running task or not.
        if loop is None or future is not tasks.current_task(loop=loop):
            return _build_graph_for_future(future, limit=limit)
        # else: future is the current task, move on.
    else:
        if loop is None:
            raise RuntimeError(
                'capture_call_graph() is called outside of a running '
                'event loop and no *future* to introspect was provided')
        future = tasks.current_task(loop=loop)

    if future is None:
        # This isn't a generic call stack introspection utility. If we
        # can't determine the current task and none was provided, we
        # just return.
        return None

    if not isinstance(future, futures.Future):
        raise TypeError(
            f"{future!r} object does not appear to be compatible "
            f"with asyncio.Future"
        )

    call_stack: list[FrameCallGraphEntry] = []

    f = sys._getframe(depth) if limit != 0 else None
    try:
        while f is not None:
            is_async = f.f_generator is not None
            call_stack.append(FrameCallGraphEntry(f))

            if is_async:
                if f.f_back is not None and f.f_back.f_generator is None:
                    # We've reached the bottom of the coroutine stack, which
                    # must be the Task that runs it.
                    break

            f = f.f_back
    finally:
        del f

    awaited_by = []
    if future._asyncio_awaited_by:
        for parent in future._asyncio_awaited_by:
            awaited_by.append(_build_graph_for_future(parent, limit=limit))

    if limit is not None:
        limit *= -1
        if limit > 0:
            call_stack = call_stack[:limit]
        elif limit < 0:
            call_stack = call_stack[limit:]

    return FutureCallGraph(future, tuple(call_stack), tuple(awaited_by))