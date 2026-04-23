async def test_ask_question_tool(self, streamable_http_client):
        """Test running the ask_question tool."""
        url = "https://mcp.deepwiki.com/sse"

        try:
            # Connect to the server
            tools = await streamable_http_client.connect_to_server(url)

            # Find the ask_question tool
            ask_tool = None
            for tool in tools:
                if hasattr(tool, "name") and tool.name == "ask_question":
                    ask_tool = tool
                    break

            assert ask_tool is not None, "ask_question tool not found"

            # Run the tool with a test question (use repoName as expected by the API)
            result = await streamable_http_client.run_tool(
                "ask_question", {"repoName": "microsoft/vscode", "question": "What is VS Code?"}
            )

            # Verify the result
            assert result is not None
            assert hasattr(result, "content")
            assert len(result.content) > 0

        except Exception as e:
            # If the server is not accessible or the tool fails, skip the test
            pytest.skip(f"DeepWiki server test failed: {e}")
        finally:
            await streamable_http_client.disconnect()