async def test_list_all_tools(self, stdio_client):
        """Test listing all available tools from the Everything server."""
        command = "npx -y @modelcontextprotocol/server-everything"

        try:
            # Connect to the server
            tools = await stdio_client.connect_to_server(command)

            # Verify we have multiple tools
            assert len(tools) >= 3  # Everything server typically has several tools

            # Check that tools have the expected attributes
            for tool in tools:
                assert hasattr(tool, "name")
                assert hasattr(tool, "description")
                assert hasattr(tool, "inputSchema")
                assert tool.name is not None
                assert len(tool.name) > 0

            # Common tools that should be available
            expected_tools = ["echo"]  # Echo is typically available
            for expected_tool in expected_tools:
                assert any(tool.name == expected_tool for tool in tools), f"Expected tool '{expected_tool}' not found"

        finally:
            await stdio_client.disconnect()