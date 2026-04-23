async def test_connect_to_everything_server(self, stdio_client):
        """Test connecting to the Everything MCP server."""
        command = "npx -y @modelcontextprotocol/server-everything"

        try:
            # Connect to the server
            tools = await stdio_client.connect_to_server(command)

            # Verify tools were returned
            assert len(tools) > 0

            # Find the echo tool
            echo_tool = None
            for tool in tools:
                if hasattr(tool, "name") and tool.name == "echo":
                    echo_tool = tool
                    break

            assert echo_tool is not None, "Echo tool not found in server tools"
            assert echo_tool.description is not None

            # Verify the echo tool has the expected input schema
            assert hasattr(echo_tool, "inputSchema")
            assert echo_tool.inputSchema is not None

        finally:
            # Clean up the connection
            await stdio_client.disconnect()