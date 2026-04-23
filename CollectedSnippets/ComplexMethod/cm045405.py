async def test_timeout_termination() -> None:
    termination = TimeoutTermination(0.1)  # 100ms timeout

    assert await termination([]) is None
    assert not termination.terminated

    await asyncio.sleep(0.2)

    assert await termination([]) is not None
    assert termination.terminated

    await termination.reset()
    assert not termination.terminated
    assert await termination([]) is None

    assert await termination([TextMessage(content="Hello", source="user")]) is None
    await asyncio.sleep(0.2)
    assert await termination([TextMessage(content="World", source="user")]) is not None