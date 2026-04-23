async def test_one_bad_tool_does_not_drop_the_other_tools_issue_11229(self):
        """One bad schema must not abort the listing; the bad tool must be logged by name."""
        good_tool_a = self._make_tool(
            "good_a",
            {"type": "object", "properties": {"q": {"type": "string"}}, "required": ["q"]},
        )
        bad_tool = self._make_tool(
            "bad_linear_like",
            {"type": "object", "properties": {"x": {"type": "string"}}},
        )
        good_tool_b = self._make_tool(
            "good_b",
            {"type": "object", "properties": {"n": {"type": "integer"}}, "required": ["n"]},
        )

        mock_stdio = AsyncMock(spec=MCPStdioClient)
        mock_stdio.connect_to_server.return_value = [good_tool_a, bad_tool, good_tool_b]
        mock_stdio._connected = True

        from lfx.schema.json_schema import create_input_schema_from_json_schema as real_converter

        def selective_converter(schema):
            if schema is bad_tool.inputSchema:
                msg = "unhashable type: 'list'"
                raise TypeError(msg)
            return real_converter(schema)

        with (
            patch("lfx.base.mcp.util.create_input_schema_from_json_schema", side_effect=selective_converter),
            patch("lfx.base.mcp.util.logger") as mock_logger,
        ):
            mode, tool_list, tool_cache = await update_tools(
                server_name="linear-like",
                server_config={"command": "fake-cmd", "args": []},
                mcp_stdio_client=mock_stdio,
            )

        loaded_names = [t.name for t in tool_list]
        assert "good_a" in loaded_names
        assert "good_b" in loaded_names
        assert "bad_linear_like" not in loaded_names
        assert set(tool_cache.keys()) == {"good_a", "good_b"}
        assert mode == "Stdio"

        all_log_calls = (
            mock_logger.error.call_args_list + mock_logger.warning.call_args_list + mock_logger.exception.call_args_list
        )
        joined = " | ".join(str(call) for call in all_log_calls)
        assert "bad_linear_like" in joined, f"failing tool name must appear in log; got: {joined!r}"