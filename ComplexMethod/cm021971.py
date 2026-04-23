async def test_tool_search(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_init_component,
    mock_create_stream: AsyncMock,
    snapshot: SnapshotAssertion,
) -> None:
    """Test tool search."""
    assert await async_setup_component(hass, "intent", {})
    assert await async_setup_component(hass, "demo", {})
    hass.config_entries.async_update_subentry(
        mock_config_entry,
        next(iter(mock_config_entry.subentries.values())),
        data={
            CONF_LLM_HASS_API: llm.LLM_API_ASSIST,
            CONF_CHAT_MODEL: "claude-sonnet-4-6",
            CONF_TOOL_SEARCH: True,
        },
    )

    tool_search_result = ToolSearchToolSearchResultBlock(
        type="tool_search_tool_search_result",
        tool_references=[
            {
                "type": "tool_reference",
                "tool_name": "HassHumidifierSetpoint",
            },
            {
                "type": "tool_reference",
                "tool_name": "HassHumidifierMode",
            },
            {
                "type": "tool_reference",
                "tool_name": "HassClimateSetTemperature",
            },
            {
                "type": "tool_reference",
                "tool_name": "HassFanSetSpeed",
            },
            {
                "type": "tool_reference",
                "tool_name": "HassSetVolume",
            },
        ],
    )

    mock_create_stream.return_value = [
        (
            *create_thinking_block(
                0,
                ["I will fetch the available", " tools"],
            ),
            *create_content_block(
                1,
                ["Sure, let me check that for you!"],
            ),
            *create_server_tool_use_block(
                2,
                "srvtoolu_12345ABC",
                "tool_search_tool_bm25",
                [
                    '{"query": "s',
                    "et humidi",
                    "fier hum",
                    'idity"',
                    ', "limit"',
                    ": 5}",
                ],
            ),
            *create_tool_search_result_block(
                3, "srvtoolu_12345ABC", tool_search_result
            ),
            *create_thinking_block(
                4,
                ["Great! All clear, let's reply to the user!"],
            ),
            *create_content_block(
                5,
                ["Yes, I can!"],
            ),
        )
    ]

    result = await conversation.async_converse(
        hass,
        "Can you set humidifier setpoint?",
        None,
        Context(),
        agent_id="conversation.claude_conversation",
    )

    chat_log = hass.data.get(conversation.chat_log.DATA_CHAT_LOGS).get(
        result.conversation_id
    )
    # Don't test the prompt because it's not deterministic
    assert chat_log.content[1:] == snapshot
    assert mock_create_stream.call_args.kwargs["messages"] == snapshot

    tools = mock_create_stream.call_args.kwargs["tools"]
    assert {
        "type": "tool_search_tool_bm25_20251119",
        "name": "tool_search_tool_bm25",
    } in tools
    for tool in tools:
        if tool["name"] in (
            "HassTurnOn",
            "HassTurnOff",
            "GetLiveContext",
            "tool_search_tool_bm25",
        ):
            assert "defer_loading" not in tool
        else:
            assert tool["defer_loading"] is True