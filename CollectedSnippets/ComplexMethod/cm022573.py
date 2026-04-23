async def test_mcp_tool_call(
    hass: HomeAssistant,
    setup_integration: None,
    mcp_url: str,
    mcp_client: Any,
    hass_supervisor_access_token: str,
) -> None:
    """Test the tool call endpoint."""

    state = hass.states.get("light.kitchen")
    assert state
    assert state.state == STATE_OFF

    async with mcp_client(hass, mcp_url, hass_supervisor_access_token) as session:
        result = await session.call_tool(
            name="HassTurnOn",
            arguments={"name": "kitchen light"},
        )

    assert not result.isError
    assert len(result.content) == 1
    assert result.content[0].type == "text"
    # The content is the raw tool call payload
    content = json.loads(result.content[0].text)
    assert content.get("data", {}).get("success")
    assert not content.get("data", {}).get("failed")

    # Verify tool call invocation
    state = hass.states.get("light.kitchen")
    assert state
    assert state.state == STATE_ON