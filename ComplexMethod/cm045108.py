async def test_sk_chat_completion_stream_with_multiple_function_calls() -> None:
    """
    This test returns two distinct function calls via streaming, each one arriving in pieces.
    We intentionally set name, plugin_name, and function_name in the later partial chunks so
    that _merge_function_call_content is triggered to update them.
    """

    async def mock_get_streaming_chat_message_contents(
        chat_history: ChatHistory,
        settings: PromptExecutionSettings,
        **kwargs: Any,
    ) -> AsyncGenerator[list["StreamingChatMessageContent"], Any]:
        # First partial chunk for call_1
        yield [
            StreamingChatMessageContent(
                choice_index=0,
                inner_content=ChatCompletionChunk(
                    id="chunk-id-1",
                    choices=[
                        Choice(
                            delta=ChoiceDelta(
                                role="assistant",
                                tool_calls=[
                                    ChoiceDeltaToolCall(
                                        index=0,
                                        id="call_1",
                                        function=ChoiceDeltaToolCallFunction(name=None, arguments='{"arg1":'),
                                        type="function",
                                    )
                                ],
                            ),
                            finish_reason=None,
                            index=0,
                        )
                    ],
                    created=1736679999,
                    model="gpt-4o-mini",
                    object="chat.completion.chunk",
                ),
                ai_model_id="gpt-4o-mini",
                role=AuthorRole.ASSISTANT,
                items=[
                    FunctionCallContent(
                        id="call_1",
                        # no plugin_name/function_name yet
                        name=None,
                        arguments='{"arg1":',
                    )
                ],
            )
        ]
        # Second partial chunk for call_1 (updates plugin_name/function_name)
        yield [
            StreamingChatMessageContent(
                choice_index=0,
                inner_content=ChatCompletionChunk(
                    id="chunk-id-2",
                    choices=[
                        Choice(
                            delta=ChoiceDelta(
                                tool_calls=[
                                    ChoiceDeltaToolCall(
                                        index=0,
                                        function=ChoiceDeltaToolCallFunction(
                                            # Provide the rest of the arguments
                                            arguments='"value1"}',
                                            name="firstFunction",
                                        ),
                                    )
                                ]
                            ),
                            finish_reason=None,
                            index=0,
                        )
                    ],
                    created=1736679999,
                    model="gpt-4o-mini",
                    object="chat.completion.chunk",
                ),
                ai_model_id="gpt-4o-mini",
                role=AuthorRole.ASSISTANT,
                items=[
                    FunctionCallContent(
                        id="call_1", plugin_name="myPlugin", function_name="firstFunction", arguments='"value1"}'
                    )
                ],
            )
        ]
        # Now partial chunk for a second call, call_2
        yield [
            StreamingChatMessageContent(
                choice_index=0,
                inner_content=ChatCompletionChunk(
                    id="chunk-id-3",
                    choices=[
                        Choice(
                            delta=ChoiceDelta(
                                tool_calls=[
                                    ChoiceDeltaToolCall(
                                        index=0,
                                        id="call_2",
                                        function=ChoiceDeltaToolCallFunction(name=None, arguments='{"arg2":"another"}'),
                                        type="function",
                                    )
                                ],
                            ),
                            finish_reason=None,
                            index=0,
                        )
                    ],
                    created=1736679999,
                    model="gpt-4o-mini",
                    object="chat.completion.chunk",
                ),
                ai_model_id="gpt-4o-mini",
                role=AuthorRole.ASSISTANT,
                items=[FunctionCallContent(id="call_2", arguments='{"arg2":"another"}')],
            )
        ]
        # Next partial chunk updates name, plugin_name, function_name for call_2
        yield [
            StreamingChatMessageContent(
                choice_index=0,
                inner_content=ChatCompletionChunk(
                    id="chunk-id-4",
                    choices=[
                        Choice(
                            delta=ChoiceDelta(
                                tool_calls=[
                                    ChoiceDeltaToolCall(
                                        index=0, function=ChoiceDeltaToolCallFunction(name="secondFunction")
                                    )
                                ]
                            ),
                            finish_reason=None,
                            index=0,
                        )
                    ],
                    created=1736679999,
                    model="gpt-4o-mini",
                    object="chat.completion.chunk",
                ),
                ai_model_id="gpt-4o-mini",
                role=AuthorRole.ASSISTANT,
                items=[
                    FunctionCallContent(
                        id="call_2",
                        name="someFancyName",
                        plugin_name="anotherPlugin",
                        function_name="secondFunction",
                    )
                ],
            )
        ]
        # Final chunk signals finish with tool_calls
        yield [
            StreamingChatMessageContent(  # type: ignore
                choice_index=0,
                inner_content=ChatCompletionChunk(
                    id="chunk-id-5",
                    choices=[Choice(delta=ChoiceDelta(), finish_reason="tool_calls", index=0)],
                    created=1736679999,
                    model="gpt-4o-mini",
                    object="chat.completion.chunk",
                    usage=CompletionUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
                ),
                ai_model_id="gpt-4o-mini",
                role=AuthorRole.ASSISTANT,
                finish_reason=FinishReason.TOOL_CALLS,
                metadata={"usage": {"prompt_tokens": 10, "completion_tokens": 5}},
            )
        ]

    # Mock SK client
    mock_client = AsyncMock(spec=AzureChatCompletion)
    mock_client.get_streaming_chat_message_contents = mock_get_streaming_chat_message_contents

    # Create adapter and kernel
    kernel = Kernel(memory=NullMemory())
    adapter = SKChatCompletionAdapter(mock_client, kernel=kernel)

    # Call create_stream with no actual tools (we just test the multiple calls)
    messages: list[LLMMessage] = [
        SystemMessage(content="You are a helpful assistant."),
        UserMessage(content="Call two different plugin functions", source="user"),
    ]

    # Collect streaming outputs
    response_chunks: list[CreateResult | str] = []
    async for chunk in adapter.create_stream(messages=messages):
        response_chunks.append(chunk)

    # The final chunk should be a CreateResult with function_calls
    assert len(response_chunks) > 0
    final_chunk = response_chunks[-1]
    assert isinstance(final_chunk, CreateResult)
    assert final_chunk.finish_reason == "function_calls"
    assert isinstance(final_chunk.content, list)
    assert len(final_chunk.content) == 2  # We expect 2 calls

    # Verify first call merged name + arguments
    first_call = final_chunk.content[0]
    assert first_call.id == "call_1"
    assert first_call.name == "myPlugin-firstFunction"  # pluginName-functionName
    assert '{"arg1":"value1"}' in first_call.arguments

    # Verify second call also merged everything
    second_call = final_chunk.content[1]
    assert second_call.id == "call_2"
    assert second_call.name == "anotherPlugin-secondFunction"
    assert '{"arg2":"another"}' in second_call.arguments