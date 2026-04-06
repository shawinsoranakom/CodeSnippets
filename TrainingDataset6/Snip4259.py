async def sse_items_string():
    yield ServerSentEvent(data="plain text data")