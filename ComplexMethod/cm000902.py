async def _iter_sdk_messages(
    client: ClaudeSDKClient,
) -> AsyncGenerator[Any, None]:
    """Yield SDK messages with heartbeat-based timeouts.

    Uses an explicit async iterator with non-cancelling heartbeats.

    CRITICAL: we must NOT cancel `__anext__()` mid-flight — doing so
    (via `asyncio.timeout` or `wait_for`) corrupts the SDK's internal
    anyio memory stream, causing `StopAsyncIteration` on the next call
    and silently dropping all in-flight tool results.  Instead, wrap
    `__anext__()` in a `Task` and use `asyncio.wait()` with a
    timeout.  On timeout we yield a heartbeat sentinel but keep the Task
    alive so it can deliver the next message.

    Yields `None` on heartbeat timeout (caller should refresh locks and
    emit heartbeat events).  Yields the raw SDK message otherwise.
    On stream end (`StopAsyncIteration`), the generator returns normally.
    Any other exception from the SDK propagates to the caller.
    """
    msg_iter = client.receive_response().__aiter__()
    pending_task: asyncio.Task[Any] | None = None

    async def _next_msg() -> Any:
        """Await the next SDK message, wrapped for use with `asyncio.Task`."""
        return await msg_iter.__anext__()

    try:
        while True:
            if pending_task is None:
                pending_task = asyncio.create_task(_next_msg())

            done, _ = await asyncio.wait({pending_task}, timeout=_HEARTBEAT_INTERVAL)

            if not done:
                yield None  # heartbeat sentinel
                continue

            pending_task = None
            try:
                yield done.pop().result()
            except StopAsyncIteration:
                return
    finally:
        if pending_task is not None and not pending_task.done():
            pending_task.cancel()
            try:
                await pending_task
            except (asyncio.CancelledError, StopAsyncIteration):
                pass