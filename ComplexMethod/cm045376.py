async def test_model_client_stream_with_tool_calls() -> None:
    mock_client = ReplayChatCompletionClient(
        [
            CreateResult(
                content=[
                    FunctionCall(id="1", name="_pass_function", arguments=r'{"input": "task"}'),
                    FunctionCall(id="3", name="_echo_function", arguments=r'{"input": "task"}'),
                ],
                finish_reason="function_calls",
                usage=RequestUsage(prompt_tokens=10, completion_tokens=5),
                cached=False,
            ),
            "Example response 2 to task",
        ]
    )
    mock_client._model_info["function_calling"] = True  # pyright: ignore
    agent = AssistantAgent(
        "test_agent",
        model_client=mock_client,
        model_client_stream=True,
        reflect_on_tool_use=True,
        tools=[_pass_function, _echo_function],
    )
    chunks: List[str] = []
    async for message in agent.run_stream(task="task"):
        if isinstance(message, TaskResult):
            assert isinstance(message.messages[-1], TextMessage)
            assert isinstance(message.messages[1], ToolCallRequestEvent)
            assert message.messages[-1].content == "Example response 2 to task"
            assert message.messages[1].content == [
                FunctionCall(id="1", name="_pass_function", arguments=r'{"input": "task"}'),
                FunctionCall(id="3", name="_echo_function", arguments=r'{"input": "task"}'),
            ]
            assert isinstance(message.messages[2], ToolCallExecutionEvent)
            assert message.messages[2].content == [
                FunctionExecutionResult(call_id="1", content="pass", is_error=False, name="_pass_function"),
                FunctionExecutionResult(call_id="3", content="task", is_error=False, name="_echo_function"),
            ]
        elif isinstance(message, ModelClientStreamingChunkEvent):
            chunks.append(message.content)
    assert "".join(chunks) == "Example response 2 to task"