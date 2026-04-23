def test_streaming_character_by_character_with_buffering(minimax_tool_parser):
    """Test character-by-character streaming with edge cases that trigger buffering."""
    # Reset streaming state
    reset_streaming_state(minimax_tool_parser)

    # Text that includes potential buffering scenarios
    buffering_text = 'Hello world<tool_calls>\n{"name": "test"}\n</tool_calls>done'

    print("\n=== Buffering character-by-character test ===")
    print(f"Text: {repr(buffering_text)}")

    all_content = []

    for i in range(1, len(buffering_text) + 1):
        current_text = buffering_text[:i]
        previous_text = buffering_text[: i - 1] if i > 1 else ""
        delta_text = buffering_text[i - 1 : i]

        result = minimax_tool_parser.extract_tool_calls_streaming(
            previous_text=previous_text,
            current_text=current_text,
            delta_text=delta_text,
            previous_token_ids=[],
            current_token_ids=[],
            delta_token_ids=[],
            request=None,
        )

        if result and hasattr(result, "content") and result.content:
            all_content.append(result.content)
            print(f"  Char {i} ({repr(delta_text)}): {repr(result.content)}")

    final_content = "".join(all_content)
    print(f"Final content: {repr(final_content)}")

    # The parser should handle the edge case where </tool_calls> appears before <tool_calls>
    assert "Hello" in final_content, "Initial 'Hello' should be preserved"
    assert "world" in final_content, (
        "Content after false closing tag should be preserved"
    )
    assert "done" in final_content, "Final content should be preserved"

    print("✓ Buffering character-by-character test passed")