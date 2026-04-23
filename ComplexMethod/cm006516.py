async def byte_stream_generator(file_input, chunk_size: int = 8192) -> AsyncGenerator[bytes, None]:
    """Convert bytes object or stream into an async generator that yields chunks."""
    if isinstance(file_input, bytes):
        # Handle bytes object
        for i in range(0, len(file_input), chunk_size):
            yield file_input[i : i + chunk_size]
    # Handle stream object
    elif hasattr(file_input, "read"):
        while True:
            chunk = await file_input.read(chunk_size) if callable(file_input.read) else file_input.read(chunk_size)
            if not chunk:
                break
            yield chunk
    else:
        # Handle async iterator
        async for chunk in file_input:
            yield chunk