def stream_story_no_async_bytes() -> Iterable[bytes]:
    for line in message.splitlines():
        yield line.encode("utf-8")