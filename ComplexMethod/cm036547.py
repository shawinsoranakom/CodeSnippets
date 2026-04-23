def test_single_tool_call_simple_args(
        self,
        request: pytest.FixtureRequest,
        tool_parser: Any,
        test_config: ToolParserTestConfig,
        streaming: bool,
    ):
        """Verify parser extracts one tool with simple arguments."""
        # Apply xfail markers if configured
        test_name = "test_single_tool_call_simple_args"
        self.apply_xfail_mark(request, test_config, test_name, streaming)

        content, tool_calls = run_tool_extraction(
            tool_parser, test_config.single_tool_call_output, streaming=streaming
        )

        # Content check (some parsers strip it)
        if test_config.single_tool_call_expected_content is not None:
            assert content == test_config.single_tool_call_expected_content

        assert len(tool_calls) == 1, f"Expected 1 tool call, got {len(tool_calls)}"
        assert tool_calls[0].type == "function"
        assert tool_calls[0].function.name == test_config.single_tool_call_expected_name

        args = json.loads(tool_calls[0].function.arguments)
        for key, value in test_config.single_tool_call_expected_args.items():
            assert args.get(key) == value, (
                f"Expected {key}={value}, got {args.get(key)}"
            )