async def test_mcp_tools_list(
    hass: HomeAssistant,
    setup_integration: None,
    mcp_url: str,
    mcp_client: Any,
    hass_supervisor_access_token: str,
) -> None:
    """Test the tools list endpoint."""

    async with mcp_client(hass, mcp_url, hass_supervisor_access_token) as session:
        result = await session.list_tools()

    # Pick a single arbitrary tool and test that description and parameters
    # are converted correctly.
    tool = next(iter(tool for tool in result.tools if tool.name == "HassTurnOn"))
    assert tool.name == "HassTurnOn"
    assert tool.description is not None
    assert tool.inputSchema
    assert tool.inputSchema.get("type") == "object"
    properties = tool.inputSchema.get("properties")
    assert properties.get("name") == {"type": "string"}