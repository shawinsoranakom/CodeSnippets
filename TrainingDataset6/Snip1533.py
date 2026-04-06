def stream_image_no_async_yield_from() -> Iterable[bytes]:
    with read_image() as image_file:
        yield from image_file