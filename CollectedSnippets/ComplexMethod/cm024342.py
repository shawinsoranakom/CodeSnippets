async def test_tts_cache() -> None:
    """Test TTSCache."""

    async def data_gen(queue: asyncio.Queue[bytes | None | Exception]):
        while chunk := await queue.get():
            if isinstance(chunk, Exception):
                raise chunk
            yield chunk

    queue = asyncio.Queue()
    cache = tts.TTSCache("test-key", "mp3", data_gen(queue))
    assert cache.cache_key == "test-key"
    assert cache.extension == "mp3"

    for i in range(10):
        queue.put_nowait(f"{i}".encode())
    queue.put_nowait(None)

    assert await cache.async_load_data() == b"0123456789"

    with pytest.raises(RuntimeError):
        await cache.async_load_data()

    # When data is loaded, we get it all in 1 chunk
    cur = 0
    async for chunk in cache.async_stream_data():
        assert chunk == b"0123456789"
        cur += 1
    assert cur == 1

    # Show we can stream the data while it's still being generated
    async def consume_cache(cache: tts.TTSCache):
        return b"".join([chunk async for chunk in cache.async_stream_data()])

    queue = asyncio.Queue()
    cache = tts.TTSCache("test-key", "mp3", data_gen(queue))

    load_data_task = asyncio.create_task(cache.async_load_data())
    consume_pre_data_loaded_task = asyncio.create_task(consume_cache(cache))
    queue.put_nowait(b"0")
    await asyncio.sleep(0)
    queue.put_nowait(b"1")
    await asyncio.sleep(0)
    consume_mid_data_task = asyncio.create_task(consume_cache(cache))
    queue.put_nowait(b"2")
    await asyncio.sleep(0)
    queue.put_nowait(None)
    consume_post_data_loaded_task = asyncio.create_task(consume_cache(cache))
    await asyncio.sleep(0)
    assert await load_data_task == b"012"
    assert await consume_post_data_loaded_task == b"012"
    assert await consume_mid_data_task == b"012"
    assert await consume_pre_data_loaded_task == b"012"

    # Now with errors
    async def consume_cache(cache: tts.TTSCache):
        return b"".join([chunk async for chunk in cache.async_stream_data()])

    queue = asyncio.Queue()
    cache = tts.TTSCache("test-key", "mp3", data_gen(queue))

    load_data_task = asyncio.create_task(cache.async_load_data())
    consume_pre_data_loaded_task = asyncio.create_task(consume_cache(cache))
    queue.put_nowait(b"0")
    await asyncio.sleep(0)
    queue.put_nowait(b"1")
    await asyncio.sleep(0)
    consume_mid_data_task = asyncio.create_task(consume_cache(cache))
    queue.put_nowait(ValueError("Boom!"))
    await asyncio.sleep(0)
    queue.put_nowait(None)
    consume_post_data_loaded_task = asyncio.create_task(consume_cache(cache))
    await asyncio.sleep(0)
    with pytest.raises(ValueError):
        assert await load_data_task == b"012"
    with pytest.raises(ValueError):
        assert await consume_post_data_loaded_task == b"012"
    with pytest.raises(ValueError):
        assert await consume_mid_data_task == b"012"
    with pytest.raises(ValueError):
        assert await consume_pre_data_loaded_task == b"012"