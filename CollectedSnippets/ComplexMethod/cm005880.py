async def test_resilience_under_many_mixed_tools(self):
        """Stress: 20 tools, 10 healthy + 10 broken with varied error types — all 10 good survive."""
        from lfx.schema.json_schema import create_input_schema_from_json_schema as real_converter

        error_types = [TypeError, AttributeError, KeyError, NameError, RecursionError]
        tools = []
        bad_schemas: dict[int, type[Exception]] = {}
        for i in range(20):
            schema = {
                "type": "object",
                "properties": {"k": {"type": "string"}},
                "required": ["k"],
            }
            tool = self._make_tool(f"tool_{i:02d}", schema)
            tools.append(tool)
            if i % 2 == 1:  # 10 odd indices fail with rotated error types
                bad_schemas[id(schema)] = error_types[(i // 2) % len(error_types)]

        def selective_converter(schema):
            err_cls = bad_schemas.get(id(schema))
            if err_cls is not None:
                msg = f"simulated {err_cls.__name__}"
                raise err_cls(msg)
            return real_converter(schema)

        mock_stdio = AsyncMock(spec=MCPStdioClient)
        mock_stdio.connect_to_server.return_value = tools
        mock_stdio._connected = True

        with patch("lfx.base.mcp.util.create_input_schema_from_json_schema", side_effect=selective_converter):
            _, tool_list, tool_cache = await update_tools(
                server_name="stress",
                server_config={"command": "fake-cmd", "args": []},
                mcp_stdio_client=mock_stdio,
            )

        loaded = {t.name for t in tool_list}
        expected_good = {f"tool_{i:02d}" for i in range(20) if i % 2 == 0}
        assert loaded == expected_good, f"expected exactly the 10 healthy tools, got {loaded}"
        assert set(tool_cache.keys()) == expected_good