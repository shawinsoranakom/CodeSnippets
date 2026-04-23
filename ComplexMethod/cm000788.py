async def test_list_tools(self, mcp_server):
        client = _make_client(mcp_server)
        await client.initialize()
        tools = await client.list_tools()

        assert len(tools) == 3

        tool_names = {t.name for t in tools}
        assert tool_names == {"get_weather", "add_numbers", "echo"}

        # Check get_weather schema
        weather = next(t for t in tools if t.name == "get_weather")
        assert weather.description == "Get current weather for a city"
        assert "city" in weather.input_schema["properties"]
        assert weather.input_schema["required"] == ["city"]

        # Check add_numbers schema
        add = next(t for t in tools if t.name == "add_numbers")
        assert "a" in add.input_schema["properties"]
        assert "b" in add.input_schema["properties"]