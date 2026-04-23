def _build_graph_for_future(
    future: futures.Future,
    *,
    limit: int | None = None,
) -> FutureCallGraph:
    if not isinstance(future, futures.Future):
        raise TypeError(
            f"{future!r} object does not appear to be compatible "
            f"with asyncio.Future"
        )

    coro = None
    if get_coro := getattr(future, 'get_coro', None):
        coro = get_coro() if limit != 0 else None

    st: list[FrameCallGraphEntry] = []
    awaited_by: list[FutureCallGraph] = []

    while coro is not None:
        if hasattr(coro, 'cr_await'):
            # A native coroutine or duck-type compatible iterator
            st.append(FrameCallGraphEntry(coro.cr_frame))
            coro = coro.cr_await
        elif hasattr(coro, 'ag_await'):
            # A native async generator or duck-type compatible iterator
            st.append(FrameCallGraphEntry(coro.cr_frame))
            coro = coro.ag_await
        else:
            break

    if future._asyncio_awaited_by:
        for parent in future._asyncio_awaited_by:
            awaited_by.append(_build_graph_for_future(parent, limit=limit))

    if limit is not None:
        if limit > 0:
            st = st[:limit]
        elif limit < 0:
            st = st[limit:]
    st.reverse()
    return FutureCallGraph(future, tuple(st), tuple(awaited_by))