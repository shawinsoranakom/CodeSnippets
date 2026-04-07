async def async_streaming(request):
    async def async_streaming_generator():
        yield b"streaming"
        yield b" "
        yield b"content"

    return StreamingHttpResponse(async_streaming_generator())