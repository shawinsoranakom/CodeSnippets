def test_tool_search_result_formatting() -> None:
    """Test that `tool_result` blocks with `tool_reference` are handled correctly."""
    # Tool search result with tool_reference blocks
    messages = [
        HumanMessage("What tools can help with weather?"),  # type: ignore[misc]
        AIMessage(  # type: ignore[misc]
            [
                {
                    "type": "server_tool_use",
                    "id": "srvtoolu_123",
                    "name": "tool_search_tool_regex",
                    "input": {"query": "weather"},
                },
                {
                    "type": "tool_result",
                    "tool_use_id": "srvtoolu_123",
                    "content": [
                        {"type": "tool_reference", "tool_name": "get_weather"},
                        {"type": "tool_reference", "tool_name": "weather_forecast"},
                    ],
                },
            ],
        ),
    ]

    _, formatted = _format_messages(messages)

    # Verify the tool_result block is preserved correctly
    assistant_msg = formatted[1]
    assert assistant_msg["role"] == "assistant"

    # Find the tool_result block
    tool_result_block = None
    for block in assistant_msg["content"]:
        if isinstance(block, dict) and block.get("type") == "tool_result":
            tool_result_block = block
            break

    assert tool_result_block is not None
    assert tool_result_block["tool_use_id"] == "srvtoolu_123"
    assert isinstance(tool_result_block["content"], list)
    assert len(tool_result_block["content"]) == 2
    assert tool_result_block["content"][0]["type"] == "tool_reference"
    assert tool_result_block["content"][0]["tool_name"] == "get_weather"
    assert tool_result_block["content"][1]["type"] == "tool_reference"
    assert tool_result_block["content"][1]["tool_name"] == "weather_forecast"