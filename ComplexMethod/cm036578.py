def test_streaming_character_by_character_output(minimax_tool_parser):
    """Test character-by-character streaming output to simulate real streaming scenarios."""
    # Reset streaming state
    reset_streaming_state(minimax_tool_parser)

    # Complete text that will be streamed character by character
    complete_text = """I'll help you with the weather analysis. <think>Let me think about this. <tool_calls>
{"name": "internal_analysis", "arguments": {"type": "thinking"}}
</tool_calls>This tool should be ignored.</think>

Now I'll get the weather information for you. <tool_calls>
{"name": "get_current_weather", "arguments": {"city": "Seattle", "state": "WA", "unit": "celsius"}}
{"name": "calculate_area", "arguments": {"shape": "rectangle", "dimensions": {"width": 10, "height": 5}}}
</tool_calls>Here are the results."""

    print("\n=== Starting character-by-character streaming test ===")
    print(f"Complete text length: {len(complete_text)} characters")

    # Track the streaming results
    content_fragments = []
    tool_calls_detected = []

    # Stream character by character
    for i in range(1, len(complete_text) + 1):
        current_text = complete_text[:i]
        previous_text = complete_text[: i - 1] if i > 1 else ""
        delta_text = complete_text[i - 1 : i]

        # Show progress every 50 characters
        if i % 50 == 0 or i == len(complete_text):
            print(f"Progress: {i}/{len(complete_text)} characters")

        # Call the streaming parser
        result = minimax_tool_parser.extract_tool_calls_streaming(
            previous_text=previous_text,
            current_text=current_text,
            delta_text=delta_text,
            previous_token_ids=[],
            current_token_ids=[],
            delta_token_ids=[],
            request=None,
        )

        # Collect results
        if result is not None:
            if hasattr(result, "content") and result.content:
                content_fragments.append(result.content)
                # Log important content fragments
                if any(
                    keyword in result.content
                    for keyword in [
                        "<think>",
                        "</think>",
                        "<tool_calls>",
                        "</tool_calls>",
                    ]
                ):
                    print(f"  Char {i}: Content fragment: {repr(result.content)}")

            if hasattr(result, "tool_calls") and result.tool_calls:
                for tool_call in result.tool_calls:
                    tool_info = {
                        "character_position": i,
                        "function_name": tool_call.function.name
                        if tool_call.function
                        else None,
                        "arguments": tool_call.function.arguments
                        if tool_call.function
                        else None,
                    }
                    tool_calls_detected.append(tool_info)
                    print(f"  Char {i}: Tool call detected: {tool_call.function.name}")
                    if tool_call.function.arguments:
                        print(f"    Arguments: {repr(tool_call.function.arguments)}")

    # Verify results
    print("\n=== Streaming Test Results ===")
    print(f"Total content fragments: {len(content_fragments)}")
    print(f"Total tool calls detected: {len(tool_calls_detected)}")

    # Reconstruct content from fragments
    reconstructed_content = "".join(content_fragments)
    print(f"Reconstructed content length: {len(reconstructed_content)}")

    # Verify thinking tags content is preserved
    assert "<think>" in reconstructed_content, (
        "Opening thinking tag should be preserved in content"
    )
    assert "</think>" in reconstructed_content, (
        "Closing thinking tag should be preserved in content"
    )

    # Verify that tool calls inside thinking tags are NOT extracted as actual tool calls
    thinking_tool_calls = [
        tc for tc in tool_calls_detected if tc["function_name"] == "internal_analysis"
    ]
    assert len(thinking_tool_calls) == 0, (
        f"Tool calls inside thinking tags should be ignored, but found: {thinking_tool_calls}"
    )

    # Verify that real tool calls outside thinking tags ARE extracted
    weather_tool_calls = [
        tc for tc in tool_calls_detected if tc["function_name"] == "get_current_weather"
    ]
    area_tool_calls = [
        tc for tc in tool_calls_detected if tc["function_name"] == "calculate_area"
    ]
    print(tool_calls_detected)
    assert len(weather_tool_calls) > 0, (
        "get_current_weather tool call should be detected"
    )
    assert len(area_tool_calls) > 0, "calculate_area tool call should be detected"

    # Verify tool call arguments are properly streamed
    weather_args_found = any(
        tc["arguments"] for tc in weather_tool_calls if tc["arguments"]
    )
    area_args_found = any(tc["arguments"] for tc in area_tool_calls if tc["arguments"])

    print(f"Weather tool call with arguments: {weather_args_found}")
    print(f"Area tool call with arguments: {area_args_found}")

    # Verify content before and after tool calls
    assert "I'll help you with the weather analysis." in reconstructed_content, (
        "Initial content should be preserved"
    )
    assert "Here are the results." in reconstructed_content, (
        "Final content should be preserved"
    )

    # Verify that <tool_calls> and </tool_calls> tags are not included in the final content
    # (they should be filtered out when not inside thinking tags)
    content_outside_thinking = reconstructed_content
    # Remove thinking tag content to check content outside
    if "<think>" in content_outside_thinking and "</think>" in content_outside_thinking:
        start_think = content_outside_thinking.find("<think>")
        end_think = content_outside_thinking.find("</think>") + len("</think>")
        content_outside_thinking = (
            content_outside_thinking[:start_think]
            + content_outside_thinking[end_think:]
        )

    # Outside thinking tags, tool_calls tags should be filtered
    tool_calls_in_content = content_outside_thinking.count("<tool_calls>")
    assert tool_calls_in_content == 0, (
        f"<tool_calls> tags should be filtered from content outside thinking tags, but found {tool_calls_in_content}"
    )

    print("\n=== Character-by-character streaming test completed successfully ===")
    print("✓ Tool calls inside thinking tags correctly ignored")
    print("✓ Tool calls outside thinking tags correctly detected")
    print("✓ Content properly streamed and reconstructed")
    print("✓ Tool call tags properly filtered from content")
    print("✓ Character-level streaming works correctly")