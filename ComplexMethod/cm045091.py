async def test_thought_field_with_tool_calls_streaming(
    thought_with_tool_call_stream_client: AzureAIChatCompletionClient,
) -> None:
    """
    Tests that when a model returns both tool calls and text content in a streaming response,
    the text content is preserved in the thought field of the final CreateResult.
    """
    chunks: List[Union[str, CreateResult]] = []
    async for chunk in thought_with_tool_call_stream_client.create_stream(
        messages=[UserMessage(content="Please call a function", source="user")],
        tools=[{"name": "test_tool"}],
    ):
        chunks.append(chunk)

    final_result = chunks[-1]
    assert isinstance(final_result, CreateResult)

    assert final_result.finish_reason == "function_calls"
    assert isinstance(final_result.content, list)
    assert isinstance(final_result.content[0], FunctionCall)
    assert final_result.content[0].name == "some_function"
    assert final_result.content[0].arguments == '{"foo": "bar"}'

    assert final_result.thought == "Let me think about what function to call."