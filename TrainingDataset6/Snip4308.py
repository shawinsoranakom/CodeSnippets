async def stream_raw() -> AsyncIterable[str]:
    """Async generator with no internal await - would hang without checkpoint."""
    i = 0
    while True:
        yield f"item {i}\n"
        i += 1