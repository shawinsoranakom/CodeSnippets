def test_extract_tool_calls(
        self, parser, model_output, expected_names, expected_args_list, expected_content
    ):
        content, tool_calls = run_tool_extraction(parser, model_output, streaming=False)
        assert content == expected_content
        assert len(tool_calls) == len(expected_names)
        for tc, name, expected_args in zip(
            tool_calls, expected_names, expected_args_list
        ):
            assert tc.type == "function"
            assert tc.function.name == name
            assert json.loads(tc.function.arguments) == expected_args
            # id format: "something:digit"
            assert tc.id.split(":")[-1].isdigit()