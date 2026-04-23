async def streaming_inner(sleep_time):
    yield b"first\n"
    await asyncio.sleep(sleep_time)
    yield b"last\n"