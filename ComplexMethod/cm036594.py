def _test_extract_tool_calls_streaming(
    tool_parser, tokenizer, model_output, tools, expected_tool_calls, expected_content
):
    other_content: str = ""
    function_names: list[str] = []
    function_args_strs: list[str] = []
    tool_call_idx: int = -1
    tool_call_ids: list[str | None] = []

    for delta_message in stream_delta_message_generator(
        tool_parser, tokenizer, model_output, tools
    ):
        # role should never be streamed from tool parser
        assert not delta_message.role

        if delta_message.content:
            other_content += delta_message.content

        streamed_tool_calls = delta_message.tool_calls

        if streamed_tool_calls and len(streamed_tool_calls) > 0:
            # make sure only one diff is present - correct even for parallel
            assert len(streamed_tool_calls) == 1
            tool_call = streamed_tool_calls[0]

            assert len(tool_parser.prev_tool_call_arr) > 0

            # if a new tool is being called, set up empty arguments
            if tool_call.index != tool_call_idx:
                tool_call_idx = tool_call.index
                function_args_strs.append("")
                tool_call_ids.append(None)

            # if a tool call ID is streamed, make sure one hasn't been already
            if tool_call.id and not tool_call_ids[tool_call.index]:
                tool_call_ids[tool_call.index] = tool_call.id

            # if parts of the function start being streamed
            if tool_call.function:
                # if the function name is defined, set it. it should be streamed
                # IN ENTIRETY, exactly one time.
                if tool_call.function.name:
                    assert isinstance(tool_call.function.name, str)
                    function_names.append(tool_call.function.name)

                if tool_call.function.arguments:
                    # make sure they're a string and then add them to the list
                    assert isinstance(tool_call.function.arguments, str)

                    function_args_strs[tool_call.index] += tool_call.function.arguments

    assert other_content == expected_content

    actual_tool_calls = [
        ToolCall(
            id=tool_call_id,
            function=FunctionCall(
                name=function_name,
                arguments=partial_json_parser.ensure_json(
                    function_args_str, Allow.OBJ | Allow.STR
                ),
            ),
        )
        for tool_call_id, function_name, function_args_str in zip(
            tool_call_ids, function_names, function_args_strs
        )
    ]
    assert_tool_calls(actual_tool_calls, expected_tool_calls)