async def test_full_flow_get_weather(self, mcp_server):
        """Full flow: discover tools, select one, execute it."""
        # Step 1: Discover tools (simulating what the frontend/API would do)
        client = _make_client(mcp_server)
        await client.initialize()
        tools = await client.list_tools()
        assert len(tools) == 3

        # Step 2: User selects "get_weather" and we get its schema
        weather_tool = next(t for t in tools if t.name == "get_weather")

        # Step 3: Execute the block — no credentials (public server)
        block = MCPToolBlock()
        input_data = MCPToolBlock.Input(
            server_url=mcp_server,
            selected_tool="get_weather",
            tool_input_schema=weather_tool.input_schema,
            tool_arguments={"city": "Paris"},
        )

        outputs = []
        async for name, data in block.run(input_data, user_id=MOCK_USER_ID):
            outputs.append((name, data))

        assert len(outputs) == 1
        assert outputs[0][0] == "result"
        result = outputs[0][1]
        assert result["city"] == "Paris"
        assert result["temperature"] == 22
        assert result["condition"] == "sunny"