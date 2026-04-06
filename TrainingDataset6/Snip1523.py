def stream_story_no_async() -> Iterable[str]:
    for line in message.splitlines():
        yield line