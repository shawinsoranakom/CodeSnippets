async def stream_story_no_annotation_bytes():
    for line in message.splitlines():
        yield line.encode("utf-8")