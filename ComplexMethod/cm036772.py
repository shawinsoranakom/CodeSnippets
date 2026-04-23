def test_single_turn_token_counting():
    """Test token counting behavior for a single turn."""
    # Create a context
    context = HarmonyContext(messages=[], available_tools=[])

    # Create a mock RequestOutput with specific token counts
    mock_output = create_mock_request_output(
        prompt_token_ids=[1, 2, 3, 4, 5],  # 5 prompt tokens
        output_token_ids=[6, 7, 8],  # 3 output tokens
        num_cached_tokens=2,  # 2 cached tokens
    )

    # Append the output to the context
    context.append_output(mock_output)

    # Verify the token counts
    assert context.num_prompt_tokens == 5
    assert context.num_output_tokens == 3
    assert context.num_cached_tokens == 2
    assert context.num_tool_output_tokens == 0  # No tool tokens in first turn

    # Verify internal state tracking
    assert not context.is_first_turn
    assert len(context.all_turn_metrics) == 1
    previous_turn = context.all_turn_metrics[0]
    assert previous_turn.input_tokens == 5
    assert previous_turn.output_tokens == 3
    assert previous_turn.cached_input_tokens == 2
    assert previous_turn.tool_output_tokens == 0