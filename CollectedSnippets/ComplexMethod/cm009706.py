def test_disable_streaming(
    *,
    disable_streaming: bool | Literal["tool_calling"],
) -> None:
    model = StreamingModel(disable_streaming=disable_streaming)
    assert model.invoke([]).content == "invoke"

    expected = "invoke" if disable_streaming is True else "stream"
    assert next(model.stream([])).content == expected
    assert (
        model.invoke([], config={"callbacks": [LogStreamCallbackHandler()]}).content
        == expected
    )

    expected = "invoke" if disable_streaming in {"tool_calling", True} else "stream"
    assert next(model.stream([], tools=[{"type": "function"}])).content == expected
    assert (
        model.invoke(
            [], config={"callbacks": [LogStreamCallbackHandler()]}, tools=[{}]
        ).content
        == expected
    )