async def test_sk_chat_completion_with_function_call_and_execution_result_messages() -> None:
    """
    Test that _convert_to_chat_history can properly handle a conversation
    that includes both an assistant function-call message and a function
    execution result message in the same sequence.
    """
    # Mock the SK client to return some placeholder response
    mock_client = AsyncMock(spec=AzureChatCompletion)
    mock_client.get_chat_message_contents = AsyncMock(
        return_value=[
            ChatMessageContent(
                ai_model_id="test-model",
                role=AuthorRole.ASSISTANT,
                items=[TextContent(text="All done!")],
                finish_reason=FinishReason.STOP,
                metadata={"usage": {"prompt_tokens": 10, "completion_tokens": 5}},
            )
        ]
    )

    adapter = SKChatCompletionAdapter(sk_client=mock_client, kernel=Kernel(memory=NullMemory()))

    # Messages include:
    #  1) SystemMessage
    #  2) UserMessage
    #  3) AssistantMessage with a function call
    #  4) FunctionExecutionResultMessage
    #  5) AssistantMessage with plain text

    messages: list[LLMMessage] = [
        SystemMessage(content="You are a helpful assistant."),
        UserMessage(content="What is 3 + 5?", source="user"),
        AssistantMessage(
            content=[
                FunctionCall(
                    id="call_1",
                    name="calculator",
                    arguments='{"a":3,"b":5}',
                )
            ],
            thought="Let me call the calculator function",
            source="assistant",
        ),
        FunctionExecutionResultMessage(
            content=[
                FunctionExecutionResult(
                    call_id="call_1",
                    name="calculator",
                    content="8",
                )
            ]
        ),
        AssistantMessage(content="The answer is 8.", source="assistant"),
    ]

    # Run create (which triggers _convert_to_chat_history internally)
    result = await adapter.create(messages=messages)

    # Verify final CreateResult
    assert isinstance(result.content, str)
    assert "All done!" in result.content
    assert result.finish_reason == "stop"

    # Ensure the underlying client was called with a properly built ChatHistory
    mock_client.get_chat_message_contents.assert_awaited_once()
    chat_history_arg = mock_client.get_chat_message_contents.call_args[0][0]  # The ChatHistory passed in

    # Expecting 5 messages in the ChatHistory
    assert len(chat_history_arg) == 6

    # 1) System message
    assert chat_history_arg[0].role == AuthorRole.SYSTEM
    assert chat_history_arg[0].items[0].text == "You are a helpful assistant."

    # 2) User message
    assert chat_history_arg[1].role == AuthorRole.USER
    assert chat_history_arg[1].items[0].text == "What is 3 + 5?"

    # 3) Assistant message with thought
    assert chat_history_arg[2].role == AuthorRole.ASSISTANT
    assert chat_history_arg[2].items[0].text == "Let me call the calculator function"

    # 4) Assistant message with function call
    assert chat_history_arg[3].role == AuthorRole.ASSISTANT
    assert chat_history_arg[3].finish_reason == FinishReason.TOOL_CALLS
    # Should have one FunctionCallContent
    func_call_contents = chat_history_arg[3].items
    assert len(func_call_contents) == 1
    assert func_call_contents[0].id == "call_1"
    assert func_call_contents[0].function_name == "calculator"
    assert func_call_contents[0].arguments == '{"a":3,"b":5}'
    assert func_call_contents[0].plugin_name == "autogen_tools"

    # 5) Function execution result message
    assert chat_history_arg[4].role == AuthorRole.TOOL
    tool_contents = chat_history_arg[4].items
    assert len(tool_contents) == 1
    assert tool_contents[0].id == "call_1"
    assert tool_contents[0].result == "8"
    assert tool_contents[0].function_name == "calculator"
    assert tool_contents[0].plugin_name == "autogen_tools"

    # 6) Assistant message with plain text
    assert chat_history_arg[5].role == AuthorRole.ASSISTANT
    assert chat_history_arg[5].items[0].text == "The answer is 8."