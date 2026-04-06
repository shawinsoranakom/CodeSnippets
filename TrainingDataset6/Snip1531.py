async def stream_image() -> AsyncIterable[bytes]:
    with read_image() as image_file:
        for chunk in image_file:
            yield chunk