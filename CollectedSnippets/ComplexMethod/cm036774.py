async def test_streaming_multi_turn_token_counting(mock_parser):
    """Test token counting for streaming multi-turn conversations.

    This test focuses on how StreamingHarmonyContext counts tokens in a
    multi-turn conversation with streaming (token-by-token) outputs and
    message boundaries.
    """
    # Create a streaming context
    context = StreamingHarmonyContext(messages=[], available_tools=["browser"])

    num_prompt_tokens = [3, 8, 13]
    num_output_tokens = [3, 3, 2]
    num_cached_tokens = [0, 3, 8]

    # Simulate three turns of conversation:
    # Turn 1: stream tokens one by one, then finish the message
    # Turn 2: new prompt, stream more tokens with a reasoning segment
    # Turn 3: new prompt with tool output and cached tokens

    # First turn: 3 tokens streamed one by one
    # First token of first turn
    context.append_output(
        create_mock_request_output(
            prompt_token_ids=[1, 2, 3],  # 3 prompt tokens
            output_token_ids=[101],  # Single token
            num_cached_tokens=num_cached_tokens[0],
            finished=False,  # Not end of message yet
        )
    )

    # Second token of first turn
    context.append_output(
        create_mock_request_output(
            output_token_ids=[102],
            finished=False,
        )
    )

    # Last token of first turn (finished=True signals end of message)
    context.append_output(
        create_mock_request_output(
            output_token_ids=[103],
            finished=True,  # End of message
        )
    )

    # Check token counts after first turn
    assert context.num_prompt_tokens == 3  # Initial prompt tokens
    assert context.num_output_tokens == 3  # Three output tokens
    assert context.num_cached_tokens == 0
    assert context.num_tool_output_tokens == 0  # No tool output in first turn
    assert context.first_tok_of_message is True  # Ready for next message

    # Second turn: reasoning tokens in analysis channel
    mock_parser.current_channel = "analysis"  # Set to reasoning channel

    # First token of second turn
    context.append_output(
        create_mock_request_output(
            prompt_token_ids=[
                1,
                2,
                3,
                101,
                102,
                103,
                4,
                5,
            ],  # 8 tokens (includes previous)
            output_token_ids=[201],
            num_cached_tokens=num_cached_tokens[1],  # Some tokens cached
            finished=False,
        )
    )

    # More tokens in reasoning channel
    context.append_output(
        create_mock_request_output(
            output_token_ids=[202],
            finished=False,
        )
    )

    context.append_output(
        create_mock_request_output(
            output_token_ids=[203],
            finished=True,  # End of reasoning message
        )
    )

    # Check counts after second turn (reasoning message)
    assert context.num_prompt_tokens == 3 + 8  # Initial + second prompt
    assert context.num_output_tokens == 3 + 3  # First turn + second turn
    assert context.num_reasoning_tokens == 3  # All tokens in analysis channel
    assert context.num_cached_tokens == 3  # Cached tokens from second turn

    # Formula: this turn prompt tokens - last turn prompt - last turn output
    expected_tool_tokens = 8 - 3 - 3  # = 2
    assert context.num_tool_output_tokens == expected_tool_tokens

    # Third turn: regular output channel
    mock_parser.current_channel = "final"  # Switch back to regular channel

    # Third turn (with more cached tokens)
    context.append_output(
        create_mock_request_output(
            prompt_token_ids=[
                1,
                2,
                3,
                101,
                102,
                103,
                4,
                5,
                201,
                202,
                203,
                6,
                7,
            ],  # 13 tokens
            output_token_ids=[301],
            num_cached_tokens=num_cached_tokens[2],  # More cached tokens
            finished=False,
        )
    )

    context.append_output(
        create_mock_request_output(
            output_token_ids=[302],
            finished=True,
        )
    )

    # Final token counts check
    assert context.num_prompt_tokens == sum(num_prompt_tokens)  # All prompts
    assert context.num_output_tokens == sum(num_output_tokens)  # All outputs
    assert context.num_reasoning_tokens == 3  # Unchanged from second turn
    assert context.num_cached_tokens == sum(
        num_cached_tokens
    )  # Accumulated cached tokens

    # Additional tool tokens from third turn
    # Formula: this turn prompt - last turn prompt - last turn output
    additional_tool_tokens = 13 - 8 - 3  # = 2
    assert (
        context.num_tool_output_tokens == expected_tool_tokens + additional_tool_tokens
    )

    # Validate all turn metrics
    assert len(context.all_turn_metrics) == 3
    for i, turn in enumerate(context.all_turn_metrics):
        assert turn.input_tokens == num_prompt_tokens[i]
        assert turn.output_tokens == num_output_tokens[i]
        assert turn.cached_input_tokens == num_cached_tokens[i]
    assert context.all_turn_metrics[1].tool_output_tokens == 2
    assert context.all_turn_metrics[2].tool_output_tokens == 2