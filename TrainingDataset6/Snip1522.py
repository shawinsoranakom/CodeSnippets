async def stream_story() -> AsyncIterable[str]:
    for line in message.splitlines():
        yield line