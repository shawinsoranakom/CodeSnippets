async def sse_items() -> AsyncIterable[Item]:
    for item in items:
        yield item