async def test_trigger_tool_call_in_chat_log(hass: HomeAssistant) -> None:
    """Test that trigger tool calls are stored in the chat log."""
    trigger_sentence = "test automation trigger"
    trigger_response = "Trigger activated!"

    manager = get_agent_manager(hass)
    callback = AsyncMock(return_value=trigger_response)
    manager.register_trigger([trigger_sentence], callback)

    result = await conversation.async_converse(
        hass, trigger_sentence, None, Context(), None
    )

    assert result.response.response_type == intent.IntentResponseType.ACTION_DONE

    with (
        chat_session.async_get_chat_session(hass, result.conversation_id) as session,
        async_get_chat_log(hass, session) as chat_log,
    ):
        pass

    # Find the tool call in the chat log
    tool_call_content: AssistantContent | None = None
    tool_result_content: ToolResultContent | None = None

    for content in chat_log.content:
        if content.role == "assistant" and content.tool_calls:
            tool_call_content = content
        if content.role == "tool_result":
            tool_result_content = content

    # Verify tool call was stored
    assert tool_call_content is not None and tool_call_content.tool_calls is not None
    assert len(tool_call_content.tool_calls) == 1
    assert tool_call_content.tool_calls[0].tool_name == "trigger_sentence"
    assert tool_call_content.tool_calls[0].external is True
    assert tool_call_content.tool_calls[0].tool_args == {}

    # Verify tool result was stored
    assert tool_result_content is not None
    assert tool_result_content.tool_name == "trigger_sentence"
    assert tool_result_content.tool_result["response"] == trigger_response