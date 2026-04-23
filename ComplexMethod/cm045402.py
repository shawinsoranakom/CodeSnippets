async def test_handoff_termination() -> None:
    termination = HandoffTermination("target")
    assert await termination([]) is None
    await termination.reset()
    assert await termination([TextMessage(content="Hello", source="user")]) is None
    await termination.reset()
    assert await termination([HandoffMessage(target="target", source="user", content="Hello")]) is not None
    assert termination.terminated
    await termination.reset()
    assert await termination([HandoffMessage(target="another", source="user", content="Hello")]) is None
    assert not termination.terminated
    await termination.reset()
    assert (
        await termination(
            [
                TextMessage(content="Hello", source="user"),
                HandoffMessage(target="target", source="user", content="Hello"),
            ]
        )
        is not None
    )
    assert termination.terminated
    await termination.reset()