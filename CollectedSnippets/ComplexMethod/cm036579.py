def test_streaming_character_by_character_simple_tool_call(minimax_tool_parser):
    """Test character-by-character streaming for a simple tool call scenario."""
    # Reset streaming state
    reset_streaming_state(minimax_tool_parser)

    # Simple tool call text
    simple_text = 'Let me check the weather. <tool_calls>\n{"name": "get_weather", "arguments": {"city": "NYC"}}\n</tool_calls>'

    print("\n=== Simple character-by-character test ===")
    print(f"Text: {repr(simple_text)}")

    content_parts = []
    tool_name_sent = False
    tool_args_sent = False

    for i in range(1, len(simple_text) + 1):
        current_text = simple_text[:i]
        previous_text = simple_text[: i - 1] if i > 1 else ""
        delta_text = simple_text[i - 1 : i]

        result = minimax_tool_parser.extract_tool_calls_streaming(
            previous_text=previous_text,
            current_text=current_text,
            delta_text=delta_text,
            previous_token_ids=[],
            current_token_ids=[],
            delta_token_ids=[],
            request=None,
        )

        if result:
            if hasattr(result, "content") and result.content:
                content_parts.append(result.content)
                print(
                    f"  Char {i} ({repr(delta_text)}): Content: {repr(result.content)}"
                )

            if hasattr(result, "tool_calls") and result.tool_calls:
                for tool_call in result.tool_calls:
                    if tool_call.function and tool_call.function.name:
                        tool_name_sent = True
                        print(f"  Char {i}: Tool name: {tool_call.function.name}")
                    if tool_call.function and tool_call.function.arguments:
                        tool_args_sent = True
                        print(
                            f"  Char {i}: Tool args: {repr(tool_call.function.arguments)}"
                        )

    # Verify basic expectations
    reconstructed_content = "".join(content_parts)
    print(f"Final reconstructed content: {repr(reconstructed_content)}")

    assert tool_name_sent, "Tool name should be sent during streaming"
    assert tool_args_sent, "Tool arguments should be sent during streaming"
    assert "Let me check the weather." in reconstructed_content, (
        "Initial content should be preserved"
    )

    print("✓ Simple character-by-character test passed")