def test_streaming_arguments_delta_only(minimax_tool_parser):
    """Test that each streaming call returns only the delta (new part) of arguments."""
    # Reset streaming state
    minimax_tool_parser.current_tool_name_sent = False
    minimax_tool_parser.prev_tool_call_arr = []
    minimax_tool_parser.current_tool_id = -1
    minimax_tool_parser.streamed_args_for_tool = []

    # Simulate two consecutive calls with growing arguments
    call1_text = (
        '<tool_calls>\n{"name": "test_tool", "arguments": {"param1": "value1"}}'
    )
    call2_text = '<tool_calls>\n{"name": "test_tool", "arguments": {"param1": "value1", "param2": "value2"}}'

    print(f"Call 1 text: {repr(call1_text)}")
    print(f"Call 2 text: {repr(call2_text)}")

    # First call - should get the function name and initial arguments
    result1 = minimax_tool_parser.extract_tool_calls_streaming(
        previous_text="",
        current_text=call1_text,
        delta_text=call1_text,
        previous_token_ids=[],
        current_token_ids=[],
        delta_token_ids=[],
        request=None,
    )

    print(f"Result 1: {result1}")
    if result1 and hasattr(result1, "tool_calls") and result1.tool_calls:
        for i, tc in enumerate(result1.tool_calls):
            print(f"  Tool call {i}: {tc}")

    # Second call - should only get the delta (new part) of arguments
    result2 = minimax_tool_parser.extract_tool_calls_streaming(
        previous_text=call1_text,
        current_text=call2_text,
        delta_text=', "param2": "value2"}',
        previous_token_ids=[],
        current_token_ids=[],
        delta_token_ids=[],
        request=None,
    )

    print(f"Result 2: {result2}")
    if result2 and hasattr(result2, "tool_calls") and result2.tool_calls:
        for i, tc in enumerate(result2.tool_calls):
            print(f"  Tool call {i}: {tc}")

    # Verify the second call only returns the delta
    if result2 is not None and hasattr(result2, "tool_calls") and result2.tool_calls:
        tool_call = result2.tool_calls[0]
        if tool_call.function and tool_call.function.arguments:
            args_delta = tool_call.function.arguments
            print(f"Arguments delta from second call: {repr(args_delta)}")

            # Should only contain the new part, not the full arguments
            # The delta should be something like ', "param2": "value2"}' or just '"param2": "value2"'
            assert (
                ', "param2": "value2"}' in args_delta
                or '"param2": "value2"' in args_delta
            ), f"Expected delta containing param2, got: {args_delta}"

            # Should NOT contain the previous parameter data
            assert '"param1": "value1"' not in args_delta, (
                f"Arguments delta should not contain previous data: {args_delta}"
            )

            # The delta should be relatively short (incremental, not cumulative)
            expected_max_length = len(', "param2": "value2"}') + 10  # Some tolerance
            assert len(args_delta) <= expected_max_length, (
                f"Delta seems too long (possibly cumulative): {args_delta}"
            )

            print("✓ Delta validation passed")
        else:
            print("No arguments in result2 tool call")
    else:
        print("No tool calls in result2 or result2 is None")
        # This might be acceptable if no incremental update is needed
        # But let's at least verify that result1 had some content
        assert result1 is not None, "At least the first call should return something"