async def test_functional_termination() -> None:
    async def async_termination_func(messages: Sequence[BaseAgentEvent | BaseChatMessage]) -> bool:
        if len(messages) < 1:
            return False
        if isinstance(messages[-1], TextMessage):
            return messages[-1].content == "stop"
        return False

    termination = FunctionalTermination(async_termination_func)
    assert await termination([]) is None
    await termination.reset()

    assert await termination([TextMessage(content="Hello", source="user")]) is None
    await termination.reset()

    assert await termination([TextMessage(content="stop", source="user")]) is not None
    assert termination.terminated
    await termination.reset()

    assert await termination([TextMessage(content="Hello", source="user")]) is None

    class TestContentType(BaseModel):
        content: str
        data: str

    def sync_termination_func(messages: Sequence[BaseAgentEvent | BaseChatMessage]) -> bool:
        if len(messages) < 1:
            return False
        last_message = messages[-1]
        if isinstance(last_message, StructuredMessage) and isinstance(last_message.content, TestContentType):  # type: ignore[reportUnknownMemberType]
            return last_message.content.data == "stop"
        return False

    termination = FunctionalTermination(sync_termination_func)
    assert await termination([]) is None
    await termination.reset()
    assert await termination([TextMessage(content="Hello", source="user")]) is None
    await termination.reset()
    assert (
        await termination(
            [StructuredMessage[TestContentType](content=TestContentType(content="1", data="stop"), source="user")]
        )
        is not None
    )
    assert termination.terminated
    await termination.reset()
    assert await termination([TextMessage(content="Hello", source="user")]) is None