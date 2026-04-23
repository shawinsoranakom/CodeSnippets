def test_variable_length_cross_attn_block_allocation():
    """Test that cross-attention blocks are allocated per-request based on
    actual encoder input length, not a fixed maximum.

    Fixed max-encoder-length allocation would assign
    `ceil(max_encoder_tokens / block_size)` blocks to
    every request whereas with dynamic allocation, exactly
    `ceil(actual_encoder_tokens / block_size)` blocks are assigned
    to each request.
    """
    block_size = 16
    scheduler = _create_encoder_decoder_scheduler(block_size=block_size)

    # Create requests with distinctly different encoder input lengths,
    # simulating variable-length audio inputs to a model like Whisper.
    encoder_lengths = [500, 1000, 200]
    num_prompt_tokens = 100  # Decoder prompt tokens

    requests = []
    for i, enc_len in enumerate(encoder_lengths):
        req = create_requests(
            num_requests=1,
            num_tokens=num_prompt_tokens,
            mm_hashes_list=[[f"enc_hash_{i}"]],
            mm_positions=[[PlaceholderRange(offset=0, length=enc_len)]],
            req_ids=[f"req_{i}"],
        )[0]
        requests.append(req)

    # Add and schedule all requests.
    for req in requests:
        scheduler.add_request(req)

    output = scheduler.schedule()

    # All requests should be scheduled.
    assert len(output.scheduled_new_reqs) == len(requests)

    # Verify cross-attention blocks per request match the actual encoder length.
    from math import ceil

    for req, enc_len in zip(requests, encoder_lengths):
        expected_blocks = ceil(enc_len / block_size)
        actual_blocks = _get_num_cross_attn_blocks(scheduler, req.request_id)

        assert actual_blocks == expected_blocks, (
            f"Request {req.request_id} with {enc_len} encoder tokens: "
            f"expected {expected_blocks} cross-attn blocks, "
            f"got {actual_blocks}"
        )

    # Verify that different encoder lengths produce different block counts,
    # confirming variable-length (not fixed-max) allocation.
    block_counts = [
        _get_num_cross_attn_blocks(scheduler, req.request_id) for req in requests
    ]
    assert len(set(block_counts)) > 1, (
        "All requests have the same number of cross-attn blocks, "
        "suggesting static max-based allocation instead of per-request"
    )