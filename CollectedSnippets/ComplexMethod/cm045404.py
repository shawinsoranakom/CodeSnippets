async def test_or_termination() -> None:
    termination = MaxMessageTermination(3) | TextMentionTermination("stop")
    assert await termination([]) is None
    await termination.reset()
    assert await termination([TextMessage(content="Hello", source="user")]) is None
    await termination.reset()
    assert (
        await termination([TextMessage(content="Hello", source="user"), TextMessage(content="World", source="agent")])
        is None
    )
    await termination.reset()
    assert (
        await termination([TextMessage(content="Hello", source="user"), TextMessage(content="stop", source="user")])
        is not None
    )
    await termination.reset()
    assert (
        await termination([TextMessage(content="Hello", source="user"), TextMessage(content="Hello", source="user")])
        is None
    )
    await termination.reset()
    assert (
        await termination(
            [
                TextMessage(content="Hello", source="user"),
                TextMessage(content="Hello", source="user"),
                TextMessage(content="Hello", source="user"),
            ]
        )
        is not None
    )
    await termination.reset()
    assert (
        await termination(
            [
                TextMessage(content="Hello", source="user"),
                TextMessage(content="Hello", source="user"),
                TextMessage(content="stop", source="user"),
            ]
        )
        is not None
    )
    await termination.reset()
    assert (
        await termination(
            [
                TextMessage(content="Hello", source="user"),
                TextMessage(content="Hello", source="user"),
                TextMessage(content="Hello", source="user"),
                TextMessage(content="stop", source="user"),
            ]
        )
        is not None
    )