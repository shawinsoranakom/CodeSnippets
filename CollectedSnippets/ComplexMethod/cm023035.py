async def test_intent_tool_call_in_chat_log(hass: HomeAssistant) -> None:
    """Test that intent tool calls are stored in the chat log."""
    hass.states.async_set(
        "light.test_light", "off", attributes={ATTR_FRIENDLY_NAME: "Test Light"}
    )
    async_mock_service(hass, "light", "turn_on")

    result = await conversation.async_converse(
        hass, "turn on test light", None, Context(), None
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
    assistant_content: AssistantContent | None = None

    for content in chat_log.content:
        if content.role == "assistant" and content.tool_calls:
            tool_call_content = content
        if content.role == "tool_result":
            tool_result_content = content
        if content.role == "assistant" and not content.tool_calls:
            assistant_content = content

    # Verify tool call was stored
    assert tool_call_content is not None and tool_call_content.tool_calls is not None
    assert len(tool_call_content.tool_calls) == 1
    assert tool_call_content.tool_calls[0].tool_name == "HassTurnOn"
    assert tool_call_content.tool_calls[0].external is True
    assert tool_call_content.tool_calls[0].tool_args.get("name") == "Test Light"

    # Verify tool result was stored
    assert tool_result_content is not None
    assert tool_result_content.tool_name == "HassTurnOn"
    assert tool_result_content.tool_result["response_type"] == "action_done"

    # Verify final assistant content with speech
    assert assistant_content is not None
    assert assistant_content.content is not None