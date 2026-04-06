async def stream_jsonl() -> AsyncIterable[int]:
    """JSONL async generator with no internal await."""
    i = 0
    while True:
        yield i
        i += 1