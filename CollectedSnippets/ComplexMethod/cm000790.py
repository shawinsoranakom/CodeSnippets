async def test_list_tools(self):
        """Verify we can discover tools from a real MCP server."""
        client = MCPClient(OPENAI_DOCS_MCP_URL)
        await client.initialize()
        tools = await client.list_tools()

        assert len(tools) >= 3  # server has at least 5 tools as of writing

        tool_names = {t.name for t in tools}
        # These tools are documented and should be stable
        assert "search_openai_docs" in tool_names
        assert "list_openai_docs" in tool_names
        assert "fetch_openai_doc" in tool_names

        # Verify schema structure
        search_tool = next(t for t in tools if t.name == "search_openai_docs")
        assert "query" in search_tool.input_schema.get("properties", {})
        assert "query" in search_tool.input_schema.get("required", [])