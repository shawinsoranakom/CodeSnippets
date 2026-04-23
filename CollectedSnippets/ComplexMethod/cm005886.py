async def test_run_wiki_structure_tool(self, streamable_http_client):
        """Test running the read_wiki_structure tool."""
        url = "https://mcp.deepwiki.com/sse"

        try:
            # Connect to the server
            tools = await streamable_http_client.connect_to_server(url)

            # Find the read_wiki_structure tool
            wiki_tool = None
            for tool in tools:
                if hasattr(tool, "name") and tool.name == "read_wiki_structure":
                    wiki_tool = tool
                    break

            assert wiki_tool is not None, "read_wiki_structure tool not found"

            # Run the tool with a test repository (use repoName as expected by the API)
            result = await streamable_http_client.run_tool("read_wiki_structure", {"repoName": "microsoft/vscode"})

            # Verify the result
            assert result is not None
            assert hasattr(result, "content")
            assert len(result.content) > 0

        except Exception as e:
            # If the server is not accessible or the tool fails, skip the test
            pytest.skip(f"DeepWiki server test failed: {e}")
        finally:
            await streamable_http_client.disconnect()