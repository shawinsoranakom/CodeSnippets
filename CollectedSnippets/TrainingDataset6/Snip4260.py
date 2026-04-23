async def sse_items_post() -> AsyncIterable[Item]:
    for item in items:
        yield item