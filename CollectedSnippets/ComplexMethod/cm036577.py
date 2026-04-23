def test_streaming_complex_scenario_with_multiple_tools(minimax_tool_parser):
    """Test complex streaming scenario: tools inside <think> tags and multiple tool calls in one group."""
    # Reset streaming state
    reset_streaming_state(minimax_tool_parser)

    # Complex scenario: tools inside thinking tags and multiple tools in one group
    test_stages: list[dict[str, Any]] = [
        {
            "stage": "Initial content",
            "previous": "",
            "current": "Let me help you with this task.",
            "delta": "Let me help you with this task.",
            "expected_content": "Let me help you with this task.",
            "expected_tool_calls": 0,
        },
        {
            "stage": "Start thinking tag",
            "previous": "Let me help you with this task.",
            "current": "Let me help you with this task.<think>I need to analyze this situation first.",
            "delta": "<think>I need to analyze this situation first.",
            "expected_content": "<think>I need to analyze this situation first.",
            "expected_tool_calls": 0,
        },
        {
            "stage": "Tool call inside thinking tag starts",
            "previous": "Let me help you with this task.<think>I need to analyze this situation first.",
            "current": "Let me help you with this task.<think>I need to analyze this situation first.<tool_calls>",
            "delta": "<tool_calls>",
            "expected_content": "<tool_calls>",  # Inside thinking tags, tool tags should be preserved as content
            "expected_tool_calls": 0,
        },
        {
            "stage": "Complete tool call inside thinking tag",
            "previous": "Let me help you with this task.<think>I need to analyze this situation first.<tool_calls>",
            "current": 'Let me help you with this task.<think>I need to analyze this situation first.<tool_calls>\n{"name": "internal_analysis", "arguments": {"query": "analyze situation"}}\n</tool_calls>',
            "delta": '\n{"name": "internal_analysis", "arguments": {"query": "analyze situation"}}\n</tool_calls>',
            "expected_content": '\n{"name": "internal_analysis", "arguments": {"query": "analyze situation"}}\n</tool_calls>',
            "expected_tool_calls": 0,  # Tools inside thinking tags should be ignored
        },
        {
            "stage": "End thinking tag",
            "previous": 'Let me help you with this task.<think>I need to analyze this situation first.<tool_calls>\n{"name": "internal_analysis", "arguments": {"query": "analyze situation"}}\n</tool_calls>',
            "current": 'Let me help you with this task.<think>I need to analyze this situation first.<tool_calls>\n{"name": "internal_analysis", "arguments": {"query": "analyze situation"}}\n</tool_calls></think>',
            "delta": "</think>",
            "expected_content": "</think>",
            "expected_tool_calls": 0,
        },
        {
            "stage": "Multiple tools group starts",
            "previous": 'Let me help you with this task.<think>I need to analyze this situation first.<tool_calls>\n{"name": "internal_analysis", "arguments": {"query": "analyze situation"}}\n</tool_calls></think>',
            "current": 'Let me help you with this task.<think>I need to analyze this situation first.<tool_calls>\n{"name": "internal_analysis", "arguments": {"query": "analyze situation"}}\n</tool_calls></think>\nNow I need to get weather information and calculate area.<tool_calls>',
            "delta": "\nNow I need to get weather information and calculate area.<tool_calls>",
            "expected_content": "\nNow I need to get weather information and calculate area.",  # <tool_calls> should be filtered
            "expected_tool_calls": 0,
        },
        {
            "stage": "First tool in group",
            "previous": 'Let me help you with this task.<think>I need to analyze this situation first.<tool_calls>\n{"name": "internal_analysis", "arguments": {"query": "analyze situation"}}\n</tool_calls></think>\nNow I need to get weather information and calculate area.<tool_calls>',
            "current": 'Let me help you with this task.<think>I need to analyze this situation first.<tool_calls>\n{"name": "internal_analysis", "arguments": {"query": "analyze situation"}}\n</tool_calls></think>\nNow I need to get weather information and calculate area.<tool_calls>\n{"name": "get_current_weather", "arguments": {"city": "Seattle", "state": "WA", "unit": "celsius"}}',
            "delta": '\n{"name": "get_current_weather", "arguments": {"city": "Seattle", "state": "WA", "unit": "celsius"}}',
            "expected_content": None,  # No content should be output when tool call is in progress
            "expected_tool_calls": 1,
            "expected_tool_name": "get_current_weather",
        },
        {
            "stage": "Second tool in group",
            "previous": 'Let me help you with this task.<think>I need to analyze this situation first.<tool_calls>\n{"name": "internal_analysis", "arguments": {"query": "analyze situation"}}\n</tool_calls></think>\nNow I need to get weather information and calculate area.<tool_calls>\n{"name": "get_current_weather", "arguments": {"city": "Seattle", "state": "WA", "unit": "celsius"}}',
            "current": 'Let me help you with this task.<think>I need to analyze this situation first.<tool_calls>\n{"name": "internal_analysis", "arguments": {"query": "analyze situation"}}\n</tool_calls></think>\nNow I need to get weather information and calculate area.<tool_calls>\n{"name": "get_current_weather", "arguments": {"city": "Seattle", "state": "WA", "unit": "celsius"}}\n{"name": "calculate_area", "arguments": {"shape": "rectangle", "dimensions": {"width": 10, "height": 5}}}',
            "delta": '\n{"name": "calculate_area", "arguments": {"shape": "rectangle", "dimensions": {"width": 10, "height": 5}}}',
            "expected_content": None,
            "expected_tool_calls": 1,
            "expected_tool_name": "calculate_area",
        },
        {
            "stage": "Complete tool calls group",
            "previous": 'Let me help you with this task.<think>I need to analyze this situation first.<tool_calls>\n{"name": "internal_analysis", "arguments": {"query": "analyze situation"}}\n</tool_calls></think>\nNow I need to get weather information and calculate area.<tool_calls>\n{"name": "get_current_weather", "arguments": {"city": "Seattle", "state": "WA", "unit": "celsius"}}\n{"name": "calculate_area", "arguments": {"shape": "rectangle", "dimensions": {"width": 10, "height": 5}}}',
            "current": 'Let me help you with this task.<think>I need to analyze this situation first.<tool_calls>\n{"name": "internal_analysis", "arguments": {"query": "analyze situation"}}\n</tool_calls></think>\nNow I need to get weather information and calculate area.<tool_calls>\n{"name": "get_current_weather", "arguments": {"city": "Seattle", "state": "WA", "unit": "celsius"}}\n{"name": "calculate_area", "arguments": {"shape": "rectangle", "dimensions": {"width": 10, "height": 5}}}</tool_calls>',
            "delta": "</tool_calls>",
            "expected_content": None,
            "expected_tool_calls": 0,
        },
    ]

    tool_calls_count = 0

    for i, test_case in enumerate(test_stages):
        print(f"\n--- Stage {i}: {test_case['stage']} ---")
        print(
            f"Previous: {repr(test_case['previous'][:100])}{'...' if len(test_case['previous']) > 100 else ''}"
        )
        print(f"Current:  {repr(test_case['current'][-100:])}")
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
        if test_case["expected_content"] is None:
            assert result is None or not getattr(result, "content", None), (
                f"Stage {i}: Expected no content output, got {result}"
            )
            print("✓ No content output as expected")
        else:
            assert result is not None and hasattr(result, "content"), (
                f"Stage {i}: Expected content output, got {result}"
            )
            assert result.content == test_case["expected_content"], (
                f"Stage {i}: Expected content {repr(test_case['expected_content'])}, got {repr(result.content)}"
            )
            print(f"✓ Content matches: {repr(result.content)}")

        # Check tool calls
        expected_tool_calls = test_case["expected_tool_calls"]
        actual_tool_calls = (
            len(result.tool_calls)
            if result and hasattr(result, "tool_calls") and result.tool_calls
            else 0
        )

        if expected_tool_calls > 0:
            assert actual_tool_calls >= expected_tool_calls, (
                f"Stage {i}: Expected at least {expected_tool_calls} tool calls, got {actual_tool_calls}"
            )

            if "expected_tool_name" in test_case:
                # Find the tool call with the expected name
                found_tool_call = None
                for tool_call in result.tool_calls:
                    if tool_call.function.name == test_case["expected_tool_name"]:
                        found_tool_call = tool_call
                        break

                assert found_tool_call is not None, (
                    f"Stage {i}: Expected tool name {test_case['expected_tool_name']} not found in tool calls: {[tc.function.name for tc in result.tool_calls]}"
                )
                print(f"✓ Tool call correct: {found_tool_call.function.name}")

                # Ensure tools inside thinking tags are not called
                assert found_tool_call.function.name != "internal_analysis", (
                    f"Stage {i}: Tool 'internal_analysis' inside thinking tags should not be called"
                )

            tool_calls_count += actual_tool_calls
            print(f"✓ Detected {actual_tool_calls} tool calls")
        else:
            assert actual_tool_calls == 0, (
                f"Stage {i}: Expected no tool calls, got {actual_tool_calls}"
            )

    # Verify overall results
    print("\n=== Test Summary ===")
    print(f"Total tool calls count: {tool_calls_count}")
    assert tool_calls_count >= 2, (
        f"Expected at least 2 valid tool calls (outside thinking tags), but got {tool_calls_count}"
    )

    print("✓ Complex streaming test completed:")
    print("  - ✓ Tools inside thinking tags correctly ignored")
    print("  - ✓ Two tool groups outside thinking tags correctly parsed")
    print("  - ✓ Content and tool call streaming correctly handled")
    print("  - ✓ Buffering mechanism works correctly")