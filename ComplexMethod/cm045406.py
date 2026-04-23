async def test_function_call_termination() -> None:
    termination = FunctionCallTermination(function_name="test_function")
    assert await termination([]) is None
    await termination.reset()

    assert await termination([TextMessage(content="Hello", source="user")]) is None
    await termination.reset()

    assert (
        await termination(
            [TextMessage(content="Hello", source="user"), ToolCallExecutionEvent(content=[], source="assistant")]
        )
        is None
    )
    await termination.reset()

    assert (
        await termination(
            [
                TextMessage(content="Hello", source="user"),
                ToolCallExecutionEvent(
                    content=[FunctionExecutionResult(content="", name="test_function", call_id="")], source="assistant"
                ),
            ]
        )
        is not None
    )
    assert termination.terminated
    await termination.reset()

    assert (
        await termination(
            [
                TextMessage(content="Hello", source="user"),
                ToolCallExecutionEvent(
                    content=[FunctionExecutionResult(content="", name="another_function", call_id="")],
                    source="assistant",
                ),
            ]
        )
        is None
    )
    assert not termination.terminated
    await termination.reset()