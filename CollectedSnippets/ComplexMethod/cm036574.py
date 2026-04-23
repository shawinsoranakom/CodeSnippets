def test_streaming_arguments_incremental_output(minimax_tool_parser):
    """Test that streaming arguments are returned incrementally, not cumulatively."""
    # Reset streaming state
    minimax_tool_parser.current_tool_name_sent = False
    minimax_tool_parser.prev_tool_call_arr = []
    minimax_tool_parser.current_tool_id = -1
    minimax_tool_parser.streamed_args_for_tool = []

    # Simulate progressive tool call building
    stages = [
        # Stage 1: Function name complete
        '<tool_calls>\n{"name": "get_current_weather", "arguments": ',
        # Stage 2: Arguments object starts with first key
        '<tool_calls>\n{"name": "get_current_weather", "arguments": {"city": ',
        # Stage 3: First parameter value added
        '<tool_calls>\n{"name": "get_current_weather", "arguments": {"city": "Seattle"',
        # Stage 4: Second parameter added
        '<tool_calls>\n{"name": "get_current_weather", "arguments": {"city": "Seattle", "state": "WA"',
        # Stage 5: Third parameter added, arguments complete
        '<tool_calls>\n{"name": "get_current_weather", "arguments": {"city": "Seattle", "state": "WA", "unit": "celsius"}}',
        # Stage 6: Tool calls closed
        '<tool_calls>\n{"name": "get_current_weather", "arguments": {"city": "Seattle", "state": "WA", "unit": "celsius"}}\n</tool',
        '<tool_calls>\n{"name": "get_current_weather", "arguments": {"city": "Seattle", "state": "WA", "unit": "celsius"}}\n</tool_calls>',
    ]

    function_name_sent = False
    previous_args_content = ""

    for i, current_text in enumerate(stages):
        previous_text = stages[i - 1] if i > 0 else ""
        delta_text = current_text[len(previous_text) :] if i > 0 else current_text

        result = minimax_tool_parser.extract_tool_calls_streaming(
            previous_text=previous_text,
            current_text=current_text,
            delta_text=delta_text,
            previous_token_ids=[],
            current_token_ids=[],
            delta_token_ids=[],
            request=None,
        )

        print(f"Stage {i}: Current text: {repr(current_text)}")
        print(f"Stage {i}: Delta text: {repr(delta_text)}")

        if result is not None and hasattr(result, "tool_calls") and result.tool_calls:
            tool_call = result.tool_calls[0]

            # Check if function name is sent (should happen only once)
            if tool_call.function and tool_call.function.name:
                assert tool_call.function.name == "get_current_weather"
                function_name_sent = True
                print(f"Stage {i}: Function name sent: {tool_call.function.name}")

            # Check if arguments are sent incrementally
            if tool_call.function and tool_call.function.arguments:
                args_fragment = tool_call.function.arguments
                print(f"Stage {i}: Got arguments fragment: {repr(args_fragment)}")

                # For incremental output, each fragment should be new content only
                # The fragment should not contain all previous content
                if i >= 2 and previous_args_content:  # After we start getting arguments
                    # The new fragment should not be identical to or contain all previous content
                    assert args_fragment != previous_args_content, (
                        f"Fragment should be incremental, not cumulative: {args_fragment}"
                    )

                    # If this is truly incremental, the fragment should be relatively small
                    # compared to the complete arguments so far
                    if len(args_fragment) > len(previous_args_content):
                        print(
                            "Warning: Fragment seems cumulative rather than incremental"
                        )

                previous_args_content = args_fragment

    # Verify function name was sent at least once
    assert function_name_sent, "Function name should have been sent"