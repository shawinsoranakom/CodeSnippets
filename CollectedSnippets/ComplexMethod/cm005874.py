def test_should_create_tools_with_prefixed_names_when_component_has_multiple_outputs():
    """Bug fix: get_tools() must handle multiple outputs with tool_name/description.

    Instead of raising ValueError, it should prefix each tool's name
    with the provided tool_name to disambiguate them.
    """
    # Arrange
    component = MultiOutputComponent()
    toolkit = ComponentToolkit(component=component)
    tool_name = "my_agent"
    tool_description = "An agent with split outputs"

    # Act
    tools = toolkit.get_tools(
        tool_name=tool_name,
        tool_description=tool_description,
    )

    # Assert — must create 2 tools with prefixed names, not raise ValueError
    assert len(tools) == 2
    tool_names = {tool.name for tool in tools}
    assert "my_agent_get_progress" in tool_names
    assert "my_agent_get_result" in tool_names
    for tool in tools:
        assert tool_description in tool.description
        assert tool.tags == [tool.name]