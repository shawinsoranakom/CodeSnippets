async def test_multi_turn_token_counting():
    """Test token counting behavior across multiple turns with tool output."""
    # Create a context
    context = HarmonyContext(messages=[], available_tools=["browser"])

    # Simulate a conversation with 3 turns
    # Turn 1: prefill 5, decode 3, tool 7
    # Turn 2: prefill 15, cached 5, decode 4, tool 1
    # Turn 3: prefill 20, cached 15, decode 5
    prompt_token_counts = [5, 15, 20]
    output_token_counts = [3, 4, 5]
    cached_token_counts = [0, 5, 15]
    mock_generator = generate_mock_outputs(
        3, prompt_token_counts, output_token_counts, cached_token_counts
    )

    # First turn - initial prompt and response
    mock_output1 = await anext(mock_generator)
    context.append_output(mock_output1)

    # At this point, we should have 5 prompt tokens and 3 output tokens
    assert context.num_prompt_tokens == 5
    assert context.num_output_tokens == 3
    assert context.num_tool_output_tokens == 0

    # Second turn - after tool output
    mock_output2 = await anext(mock_generator)
    context.append_output(mock_output2)
    # Current prompt tokens (15) - last_turn_input_tokens (5) -
    # last_turn_output_tokens (3) = 7
    expected_tool_output = 7

    assert context.num_prompt_tokens == 5 + 15
    assert context.num_output_tokens == 3 + 4
    assert context.num_tool_output_tokens == expected_tool_output
    assert context.num_cached_tokens == 5

    # Third turn - final response
    mock_output3 = await anext(mock_generator)
    context.append_output(mock_output3)
    # Additional tool output tokens from third turn:
    # Current prompt (20) - last_turn_input_tokens (15) -
    # last_turn_output_tokens (4) = 1
    expected_tool_output = 7 + 1

    assert context.num_prompt_tokens == 5 + 15 + 20
    assert context.num_output_tokens == 3 + 4 + 5
    assert context.num_tool_output_tokens == expected_tool_output
    assert context.num_cached_tokens == 5 + 15

    # Validate all turn metrics
    assert len(context.all_turn_metrics) == 3
    for i, turn in enumerate(context.all_turn_metrics):
        assert turn.input_tokens == prompt_token_counts[i]
        assert turn.output_tokens == output_token_counts[i]
        assert turn.cached_input_tokens == cached_token_counts[i]
    assert context.all_turn_metrics[1].tool_output_tokens == 7
    assert context.all_turn_metrics[2].tool_output_tokens == 1