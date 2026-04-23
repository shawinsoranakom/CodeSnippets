async def acompress_sequence(sequence, *, max_random_bytes=None):
    buf = StreamingBuffer()
    filename = _get_random_filename(max_random_bytes) if max_random_bytes else None
    with GzipFile(
        filename=filename, mode="wb", compresslevel=6, fileobj=buf, mtime=0
    ) as zfile:
        # Output headers...
        yield buf.read()
        async for item in sequence:
            zfile.write(item)
            zfile.flush()
            data = buf.read()
            if data:
                yield data
    yield buf.read()