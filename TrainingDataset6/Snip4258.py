async def sse_items_mixed() -> AsyncIterable[Item]:
    yield items[0]
    yield ServerSentEvent(data="custom-event", event="special")
    yield items[1]