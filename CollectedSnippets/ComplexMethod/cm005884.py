async def test_run_echo_tool(self, stdio_client):
        """Test running the echo tool from the Everything server."""
        command = "npx -y @modelcontextprotocol/server-everything"

        try:
            # Connect to the server
            tools = await stdio_client.connect_to_server(command)

            # Find the echo tool
            echo_tool = None
            for tool in tools:
                if hasattr(tool, "name") and tool.name == "echo":
                    echo_tool = tool
                    break

            assert echo_tool is not None, "Echo tool not found"

            # Run the echo tool
            test_message = "Hello, MCP!"
            result = await stdio_client.run_tool("echo", {"message": test_message})

            # Verify the result
            assert result is not None
            assert hasattr(result, "content")
            assert len(result.content) > 0

            # Check that the echo worked - content should contain our message
            content_text = str(result.content[0])
            assert test_message in content_text or "Echo:" in content_text

        finally:
            await stdio_client.disconnect()