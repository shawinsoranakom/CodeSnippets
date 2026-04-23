def test_streaming_thinking_tag_buffering(minimax_tool_parser):
    """Test that tool calls within thinking tags are properly handled during streaming."""
    # Reset streaming state
    minimax_tool_parser.current_tool_name_sent = False
    minimax_tool_parser.prev_tool_call_arr = []
    minimax_tool_parser.current_tool_id = -1
    minimax_tool_parser.streamed_args_for_tool = []
    # Reset buffering state
    minimax_tool_parser.pending_buffer = ""
    minimax_tool_parser.in_thinking_tag = False
    minimax_tool_parser.thinking_depth = 0

    # Test scenario: tool calls within thinking tags should be ignored
    test_cases: list[dict[str, Any]] = [
        {
            "stage": "Start thinking",
            "previous": "",
            "current": "<think>I need to use a tool. <tool_calls>",
            "delta": "<think>I need to use a tool. <tool_calls>",
            "expected_content": "<think>I need to use a tool. <tool_calls>",  # Should pass through as content
        },
        {
            "stage": "Tool call in thinking",
            "previous": "<think>I need to use a tool. <tool_calls>",
            "current": '<think>I need to use a tool. <tool_calls>\n{"name": "ignored_tool", "arguments": {"param": "value"}}\n</tool_calls>',
            "delta": '\n{"name": "ignored_tool", "arguments": {"param": "value"}}\n</tool_calls>',
            "expected_content": '\n{"name": "ignored_tool", "arguments": {"param": "value"}}\n</tool_calls>',  # </tool_calls> should be preserved in thinking tags
        },
        {
            "stage": "Real tool call after thinking",
            "previous": '<think>I need to use a tool. <tool_calls>\n{"name": "ignored_tool", "arguments": {"param": "value"}}\n</tool_calls></think>',
            "current": '<think>I need to use a tool. <tool_calls>\n{"name": "ignored_tool", "arguments": {"param": "value"}}\n</tool_calls></think>\n<tool_calls>',
            "delta": "\n<tool_calls>",
            "expected_content": "\n",  # Should output '\n' and suppress <tool_calls>
        },
    ]

    for i, test_case in enumerate(test_cases):
        print(f"\n--- Stage {i}: {test_case['stage']} ---")
        print(f"Previous: {repr(test_case['previous'])}")
        print(f"Current:  {repr(test_case['current'])}")
        print(f"Delta:    {repr(test_case['delta'])}")

        result = minimax_tool_parser.extract_tool_calls_streaming(
            previous_text=test_case["previous"],
            current_text=test_case["current"],
            delta_text=test_case["delta"],
            previous_token_ids=[],
            current_token_ids=[],
            delta_token_ids=[],
            request=None,
        )

        print(f"Result: {result}")

        # Check expected content
        if "expected_content" in test_case:
            if test_case["expected_content"] is None:
                assert result is None or not getattr(result, "content", None), (
                    f"Stage {i}: Expected no content, got {result}"
                )
            else:
                assert result is not None and hasattr(result, "content"), (
                    f"Stage {i}: Expected content, got {result}"
                )
                assert result.content == test_case["expected_content"], (
                    f"Stage {i}: Expected content {test_case['expected_content']}, got {result.content}"
                )
                print(f"✓ Content matches: {repr(result.content)}")

        # Check tool calls
        if test_case.get("expected_tool_call"):
            assert (
                result is not None
                and hasattr(result, "tool_calls")
                and result.tool_calls
            ), f"Stage {i}: Expected tool call, got {result}"

            tool_call = result.tool_calls[0]
            assert tool_call.function.name == "real_tool", (
                f"Expected real_tool, got {tool_call.function.name}"
            )
            print(f"✓ Real tool call detected: {tool_call.function.name}")

    print("✓ Thinking tag buffering test completed successfully")