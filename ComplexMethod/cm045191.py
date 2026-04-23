def test_mcp_tool_override_model() -> None:
    """Test ToolOverride model functionality for MCP."""

    # Test with both fields
    override1 = ToolOverride(name="new_name", description="new_desc")
    assert override1.name == "new_name"
    assert override1.description == "new_desc"

    # Test with only name
    override2 = ToolOverride(name="new_name")
    assert override2.name == "new_name"
    assert override2.description is None

    # Test with only description
    override3 = ToolOverride(description="new_desc")
    assert override3.name is None
    assert override3.description == "new_desc"

    # Test empty
    override4 = ToolOverride()
    assert override4.name is None
    assert override4.description is None