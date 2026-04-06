def stream_image_no_async_no_annotation():
    with read_image() as image_file:
        for chunk in image_file:
            yield chunk