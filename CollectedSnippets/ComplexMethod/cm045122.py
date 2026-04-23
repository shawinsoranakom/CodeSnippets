async def test_tool_calling(monkeypatch: pytest.MonkeyPatch) -> None:
    model = "gpt-4.1-nano-2025-04-14"
    chat_completions = [
        # Successful completion, single tool call
        ChatCompletion(
            id="id1",
            choices=[
                Choice(
                    finish_reason="tool_calls",
                    index=0,
                    message=ChatCompletionMessage(
                        content=None,
                        tool_calls=[
                            ChatCompletionMessageToolCall(
                                id="1",
                                type="function",
                                function=Function(
                                    name="_pass_function",
                                    arguments=json.dumps({"input": "task"}),
                                ),
                            )
                        ],
                        role="assistant",
                    ),
                )
            ],
            created=0,
            model=model,
            object="chat.completion",
            usage=CompletionUsage(prompt_tokens=10, completion_tokens=5, total_tokens=0),
        ),
        # Successful completion, parallel tool calls
        ChatCompletion(
            id="id2",
            choices=[
                Choice(
                    finish_reason="tool_calls",
                    index=0,
                    message=ChatCompletionMessage(
                        content=None,
                        tool_calls=[
                            ChatCompletionMessageToolCall(
                                id="1",
                                type="function",
                                function=Function(
                                    name="_pass_function",
                                    arguments=json.dumps({"input": "task"}),
                                ),
                            ),
                            ChatCompletionMessageToolCall(
                                id="2",
                                type="function",
                                function=Function(
                                    name="_fail_function",
                                    arguments=json.dumps({"input": "task"}),
                                ),
                            ),
                            ChatCompletionMessageToolCall(
                                id="3",
                                type="function",
                                function=Function(
                                    name="_echo_function",
                                    arguments=json.dumps({"input": "task"}),
                                ),
                            ),
                        ],
                        role="assistant",
                    ),
                )
            ],
            created=0,
            model=model,
            object="chat.completion",
            usage=CompletionUsage(prompt_tokens=10, completion_tokens=5, total_tokens=0),
        ),
        # Warning completion when finish reason is not tool_calls.
        ChatCompletion(
            id="id3",
            choices=[
                Choice(
                    finish_reason="stop",
                    index=0,
                    message=ChatCompletionMessage(
                        content=None,
                        tool_calls=[
                            ChatCompletionMessageToolCall(
                                id="1",
                                type="function",
                                function=Function(
                                    name="_pass_function",
                                    arguments=json.dumps({"input": "task"}),
                                ),
                            )
                        ],
                        role="assistant",
                    ),
                )
            ],
            created=0,
            model=model,
            object="chat.completion",
            usage=CompletionUsage(prompt_tokens=10, completion_tokens=5, total_tokens=0),
        ),
        # Thought field is populated when content is not None.
        ChatCompletion(
            id="id4",
            choices=[
                Choice(
                    finish_reason="tool_calls",
                    index=0,
                    message=ChatCompletionMessage(
                        content="I should make a tool call.",
                        tool_calls=[
                            ChatCompletionMessageToolCall(
                                id="1",
                                type="function",
                                function=Function(
                                    name="_pass_function",
                                    arguments=json.dumps({"input": "task"}),
                                ),
                            )
                        ],
                        role="assistant",
                    ),
                )
            ],
            created=0,
            model=model,
            object="chat.completion",
            usage=CompletionUsage(prompt_tokens=10, completion_tokens=5, total_tokens=0),
        ),
        # Should not be returning tool calls when the tool_calls are empty
        ChatCompletion(
            id="id5",
            choices=[
                Choice(
                    finish_reason="stop",
                    index=0,
                    message=ChatCompletionMessage(
                        content="I should make a tool call.",
                        tool_calls=[],
                        role="assistant",
                    ),
                )
            ],
            created=0,
            model=model,
            object="chat.completion",
            usage=CompletionUsage(prompt_tokens=10, completion_tokens=5, total_tokens=0),
        ),
        # Should raise warning when function arguments is not a string.
        ChatCompletion(
            id="id6",
            choices=[
                Choice(
                    finish_reason="tool_calls",
                    index=0,
                    message=ChatCompletionMessage(
                        content=None,
                        tool_calls=[
                            ChatCompletionMessageToolCall(
                                id="1",
                                type="function",
                                function=Function.construct(name="_pass_function", arguments={"input": "task"}),  # type: ignore
                            )
                        ],
                        role="assistant",
                    ),
                )
            ],
            created=0,
            model=model,
            object="chat.completion",
            usage=CompletionUsage(prompt_tokens=10, completion_tokens=5, total_tokens=0),
        ),
    ]

    class _MockChatCompletion:
        def __init__(self, completions: List[ChatCompletion]):
            self.completions = list(completions)
            self.calls: List[Dict[str, Any]] = []

        async def mock_create(
            self, *args: Any, **kwargs: Any
        ) -> ChatCompletion | AsyncGenerator[ChatCompletionChunk, None]:
            if kwargs.get("stream", False):
                raise NotImplementedError("Streaming not supported in this test.")
            self.calls.append(kwargs)
            return self.completions.pop(0)

    mock = _MockChatCompletion(chat_completions)
    monkeypatch.setattr(AsyncCompletions, "create", mock.mock_create)
    pass_tool = FunctionTool(_pass_function, description="pass tool.")
    fail_tool = FunctionTool(_fail_function, description="fail tool.")
    echo_tool = FunctionTool(_echo_function, description="echo tool.")
    model_client = OpenAIChatCompletionClient(model=model, api_key="")

    # Single tool call
    create_result = await model_client.create(messages=[UserMessage(content="Hello", source="user")], tools=[pass_tool])
    assert create_result.content == [FunctionCall(id="1", arguments=r'{"input": "task"}', name="_pass_function")]
    # Verify that the tool schema was passed to the model client.
    kwargs = mock.calls[0]
    assert kwargs["tools"] == [{"function": pass_tool.schema, "type": "function"}]
    # Verify finish reason
    assert create_result.finish_reason == "function_calls"

    # Parallel tool calls
    create_result = await model_client.create(
        messages=[UserMessage(content="Hello", source="user")], tools=[pass_tool, fail_tool, echo_tool]
    )
    assert create_result.content == [
        FunctionCall(id="1", arguments=r'{"input": "task"}', name="_pass_function"),
        FunctionCall(id="2", arguments=r'{"input": "task"}', name="_fail_function"),
        FunctionCall(id="3", arguments=r'{"input": "task"}', name="_echo_function"),
    ]
    # Verify that the tool schema was passed to the model client.
    kwargs = mock.calls[1]
    assert kwargs["tools"] == [
        {"function": pass_tool.schema, "type": "function"},
        {"function": fail_tool.schema, "type": "function"},
        {"function": echo_tool.schema, "type": "function"},
    ]
    # Verify finish reason
    assert create_result.finish_reason == "function_calls"

    # Warning completion when finish reason is not tool_calls.
    with pytest.warns(UserWarning, match="Finish reason mismatch"):
        create_result = await model_client.create(
            messages=[UserMessage(content="Hello", source="user")], tools=[pass_tool]
        )
        assert create_result.content == [FunctionCall(id="1", arguments=r'{"input": "task"}', name="_pass_function")]
        assert create_result.finish_reason == "function_calls"

    # Thought field is populated when content is not None.
    create_result = await model_client.create(messages=[UserMessage(content="Hello", source="user")], tools=[pass_tool])
    assert create_result.content == [FunctionCall(id="1", arguments=r'{"input": "task"}', name="_pass_function")]
    assert create_result.finish_reason == "function_calls"
    assert create_result.thought == "I should make a tool call."

    # Should not be returning tool calls when the tool_calls are empty
    create_result = await model_client.create(messages=[UserMessage(content="Hello", source="user")], tools=[pass_tool])
    assert create_result.content == "I should make a tool call."
    assert create_result.finish_reason == "stop"

    # Should raise warning when function arguments is not a string.
    with pytest.warns(UserWarning, match="Tool call function arguments field is not a string"):
        create_result = await model_client.create(
            messages=[UserMessage(content="Hello", source="user")], tools=[pass_tool]
        )
        assert create_result.content == [FunctionCall(id="1", arguments=r'{"input": "task"}', name="_pass_function")]
        assert create_result.finish_reason == "function_calls"