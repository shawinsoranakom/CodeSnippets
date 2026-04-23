async def _astream_with_chunk_timeout(
    source: AsyncIterator[T],
    timeout: float | None,
    *,
    model_name: str | None = None,
) -> AsyncIterator[T]:
    """Yield from `source` but bound the per-chunk wait time.

    If `timeout` is None or <=0, yields directly with no wall-clock bound.
    Otherwise, each `__anext__` is wrapped in
    `asyncio.wait_for(..., timeout)`. A timeout raises
    `StreamChunkTimeoutError` (a `TimeoutError` subclass) whose message
    names the knob, the env-var override, the model, and how many chunks
    were received before the stall. A single-line structured log also
    fires at WARNING so the signal is visible in aggregate logging systems
    even when the exception is caught upstream.

    When the timeout is active, the source iterator is explicitly
    `aclose()`-d on early exit (timeout, consumer break, any exception) so
    the underlying httpx streaming connection is released promptly. The
    pass-through branch (timeout disabled) relies on httpx's GC-driven
    cleanup instead — matching the behavior of unwrapped streams.
    """
    if not timeout or timeout <= 0:
        async for item in source:
            yield item
        return

    chunks_received = 0
    it = source.__aiter__()
    try:
        while True:
            try:
                chunk = await asyncio.wait_for(it.__anext__(), timeout=timeout)
            except StopAsyncIteration:
                return
            except asyncio.TimeoutError as e:
                logger.warning(
                    "langchain_openai.stream_chunk_timeout fired",
                    extra={
                        "source": "stream_chunk_timeout",
                        "timeout_s": timeout,
                        "model_name": model_name,
                        "chunks_received": chunks_received,
                    },
                )
                raise StreamChunkTimeoutError(
                    timeout,
                    model_name=model_name,
                    chunks_received=chunks_received,
                ) from e
            chunks_received += 1
            yield chunk
    finally:
        aclose = getattr(it, "aclose", None)
        if aclose is not None:
            try:
                await aclose()
            except Exception as cleanup_exc:
                # Best-effort cleanup; don't mask the original exception,
                # but leave a DEBUG trace so pool/transport bugs stay
                # discoverable at the right log level.
                logger.debug(
                    "aclose() during _astream_with_chunk_timeout cleanup "
                    "raised; ignoring",
                    exc_info=cleanup_exc,
                )