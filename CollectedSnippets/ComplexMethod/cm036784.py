def verify_chat_response(
    response: ChatCompletionResponse,
    content: str | None = None,
    reasoning: str | None = None,
    tool_calls: list[tuple[str, str]] | None = None,
):
    assert len(response.choices) == 1
    message = response.choices[0].message

    if content is not None:
        assert message.content == content
    else:
        assert not message.content

    if reasoning is not None:
        assert message.reasoning == reasoning
    else:
        assert not message.reasoning

    if tool_calls:
        assert message.tool_calls is not None
        assert len(message.tool_calls) == len(tool_calls)
        for tc, (expected_name, expected_args) in zip(message.tool_calls, tool_calls):
            assert tc.function.name == expected_name
            assert tc.function.arguments == expected_args
    else:
        assert not message.tool_calls