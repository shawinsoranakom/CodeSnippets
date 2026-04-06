def stream_image_no_async() -> Iterable[bytes]:
    with read_image() as image_file:
        for chunk in image_file:
            yield chunk