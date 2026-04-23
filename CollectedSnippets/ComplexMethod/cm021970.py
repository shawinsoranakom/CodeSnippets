async def test_function_call(
    mock_get_tools,
    hass: HomeAssistant,
    mock_config_entry_with_assist: MockConfigEntry,
    mock_init_component,
    mock_create_stream: AsyncMock,
    tool_call_json_parts: list[str],
    expected_call_tool_args: dict[str, Any],
) -> None:
    """Test function call from the assistant."""
    agent_id = "conversation.claude_conversation"
    context = Context()

    mock_tool = AsyncMock()
    mock_tool.name = "test_tool"
    mock_tool.description = "Test function"
    mock_tool.parameters = vol.Schema(
        {vol.Optional("param1", description="Test parameters"): str}
    )
    mock_tool.async_call.return_value = "Test response"

    mock_get_tools.return_value = [mock_tool]

    mock_create_stream.return_value = [
        (
            *create_content_block(0, ["Certainly, calling it now!"]),
            *create_tool_use_block(
                1,
                "toolu_0123456789AbCdEfGhIjKlM",
                "test_tool",
                tool_call_json_parts,
            ),
        ),
        create_content_block(0, ["I have ", "successfully called ", "the function"]),
    ]

    result = await conversation.async_converse(
        hass,
        "Please call the test function",
        None,
        context,
        agent_id=agent_id,
    )

    system = mock_create_stream.mock_calls[1][2]["system"]
    assert isinstance(system, list)
    system_text = " ".join(block["text"] for block in system if "text" in block)
    assert "You are a voice assistant for Home Assistant." in system_text

    assert result.response.response_type == intent.IntentResponseType.ACTION_DONE
    assert (
        result.response.speech["plain"]["speech"]
        == "I have successfully called the function"
    )
    assert mock_create_stream.mock_calls[1][2]["messages"][2] == {
        "role": "user",
        "content": [
            {
                "content": '"Test response"',
                "tool_use_id": "toolu_0123456789AbCdEfGhIjKlM",
                "type": "tool_result",
            }
        ],
    }
    mock_tool.async_call.assert_awaited_once_with(
        hass,
        llm.ToolInput(
            id="toolu_0123456789AbCdEfGhIjKlM",
            tool_name="test_tool",
            tool_args=expected_call_tool_args,
        ),
        llm.LLMContext(
            platform="anthropic",
            context=context,
            language="en",
            assistant="conversation",
            device_id=None,
        ),
    )