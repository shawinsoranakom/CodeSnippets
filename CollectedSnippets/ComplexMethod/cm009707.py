async def test_disable_streaming_async(
    *,
    disable_streaming: bool | Literal["tool_calling"],
) -> None:
    model = StreamingModel(disable_streaming=disable_streaming)
    assert (await model.ainvoke([])).content == "invoke"

    expected = "invoke" if disable_streaming is True else "stream"
    async for c in model.astream([]):
        assert c.content == expected
        break
    assert (
        await model.ainvoke([], config={"callbacks": [_AstreamEventsCallbackHandler()]})
    ).content == expected

    expected = "invoke" if disable_streaming in {"tool_calling", True} else "stream"
    async for c in model.astream([], tools=[{}]):
        assert c.content == expected
        break
    assert (
        await model.ainvoke(
            [], config={"callbacks": [_AstreamEventsCallbackHandler()]}, tools=[{}]
        )
    ).content == expected