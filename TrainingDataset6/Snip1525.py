def stream_story_no_async_no_annotation():
    for line in message.splitlines():
        yield line