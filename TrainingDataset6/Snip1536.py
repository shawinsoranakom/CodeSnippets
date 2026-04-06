async def stream_items() -> AsyncIterable[Item]:
    for item in items:
        yield item