async def test_text_message_termination() -> None:
    termination = TextMessageTermination()
    assert await termination([]) is None
    await termination.reset()
    assert await termination([StopMessage(content="Hello", source="user")]) is None
    await termination.reset()
    assert await termination([TextMessage(content="Hello", source="user")]) is not None
    assert termination.terminated
    await termination.reset()
    assert (
        await termination([StopMessage(content="Hello", source="user"), TextMessage(content="World", source="agent")])
        is not None
    )
    assert termination.terminated
    with pytest.raises(TerminatedException):
        await termination([TextMessage(content="Hello", source="user")])

    termination = TextMessageTermination(source="user")
    assert await termination([]) is None
    await termination.reset()
    assert await termination([TextMessage(content="Hello", source="user")]) is not None
    assert termination.terminated
    await termination.reset()

    termination = TextMessageTermination(source="agent")
    assert await termination([]) is None
    await termination.reset()
    assert await termination([TextMessage(content="Hello", source="user")]) is None
    await termination.reset()
    assert await termination([TextMessage(content="Hello", source="agent")]) is not None
    assert termination.terminated