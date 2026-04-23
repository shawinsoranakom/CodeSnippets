def test_get_tool_description(self):
        pytest.importorskip("mcp")

        server = MCPToolServer()
        tool1 = ToolDescription.new(
            name="tool1", description="First", parameters={"type": "object"}
        )
        tool2 = ToolDescription.new(
            name="tool2", description="Second", parameters={"type": "object"}
        )
        tool3 = ToolDescription.new(
            name="tool3", description="Third", parameters={"type": "object"}
        )

        server.harmony_tool_descriptions = {
            "test_server": ToolNamespaceConfig(
                name="test_server",
                description="test",
                tools=[tool1, tool2, tool3],
            )
        }

        # Nonexistent server
        assert server.get_tool_description("nonexistent") is None

        # None (no filter) - returns all tools
        result = server.get_tool_description("test_server", allowed_tools=None)
        assert len(result.tools) == 3

        # Filter to specific tools
        result = server.get_tool_description(
            "test_server", allowed_tools=["tool1", "tool3"]
        )
        assert len(result.tools) == 2
        assert result.tools[0].name == "tool1"
        assert result.tools[1].name == "tool3"

        # Single tool
        result = server.get_tool_description("test_server", allowed_tools=["tool2"])
        assert len(result.tools) == 1
        assert result.tools[0].name == "tool2"

        # No matching tools - returns None
        result = server.get_tool_description(
            "test_server", allowed_tools=["nonexistent"]
        )
        assert result is None

        # Empty list - returns None
        assert server.get_tool_description("test_server", allowed_tools=[]) is None