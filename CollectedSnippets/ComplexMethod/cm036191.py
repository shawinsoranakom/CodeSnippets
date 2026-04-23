def test_set_inputs_first_pass_parallel_drafting():
    """
    Test for set_inputs_first_pass with parallel drafting (extra input slots,
    with shift).

    This tests the path where needs_extra_input_slots=True and
    shift_input_ids=True (parallel drafting case). In this case:
    - Input IDs ARE shifted (like default EAGLE)
    - Each request gets extra_slots_per_request (3) new slots
    - Parallel drafting tokens are inserted and marked as masked
    - Hidden states are mapped correctly

    Setup:
    - 2 requests with query_lens [4, 4] (1 bonus + 3 spec tokens each)
    - Request 0: tokens [10, 11, 12, 13] at positions [5, 6, 7, 8]
      - Only tokens [10, 11, 12] are "valid", token 13 is rejected
    - Request 1: tokens [20, 21, 22, 23] at positions [10, 11, 12, 13], all valid.
    - next_token_ids: [100, 200] (bonus tokens)

    With shift_input_ids=True, extra_slots_per_request=3:
    Expected output layout:
    Request 0 (6 output slots = 4 - 1 + 3):
      - idx 0-2: shifted tokens [11, 12, 100]
      - idx 3-4: parallel_drafting_tokens, is_masked=True
      - idx 5: padding_token, is_rejected=True
    Request 1 (6 output slots = 4 - 1 + 3):
      - idx 6-8: shifted tokens [21, 22, 23]
      - idx 9: bonus token 200
      - idx 10-11: parallel_drafting_tokens, is_masked=True
    """
    device = torch.device(DEVICE_TYPE)

    num_speculative_tokens = 3
    block_size = BLOCK_SIZE

    proposer = _create_proposer("eagle", num_speculative_tokens, parallel_drafting=True)

    # Override to simulate parallel drafting behavior
    proposer.parallel_drafting_token_id = -2
    proposer.parallel_drafting_hidden_state_tensor = torch.zeros(
        proposer.hidden_size, dtype=proposer.dtype, device=device
    )
    proposer.is_rejected_token_mask = torch.zeros(
        proposer.max_num_tokens, dtype=torch.bool, device=device
    )
    proposer.is_masked_token_mask = torch.zeros(
        proposer.max_num_tokens, dtype=torch.bool, device=device
    )

    # Mock draft_attn_groups
    mock_kv_cache_spec = mock.MagicMock()
    mock_kv_cache_spec.block_size = block_size
    mock_attn_group = mock.MagicMock()
    mock_attn_group.kv_cache_spec = mock_kv_cache_spec
    proposer.draft_attn_groups = [mock_attn_group]

    # Request 0: query_len=4 (1 rejected), Request 1: query_len=4 (all valid)
    batch_spec = BatchSpec(
        seq_lens=[9, 14],
        query_lens=[4, 4],
    )

    common_attn_metadata = create_common_attn_metadata(
        batch_spec,
        block_size=block_size,
        device=device,
        arange_block_indices=True,
    )

    # Input tensors
    target_token_ids = torch.tensor(
        [10, 11, 12, 13, 20, 21, 22, 23], dtype=torch.int32, device=device
    )
    target_positions = torch.tensor(
        [5, 6, 7, 8, 10, 11, 12, 13], dtype=torch.int64, device=device
    )
    target_hidden_states = torch.arange(
        8 * proposer.hidden_size, dtype=proposer.dtype, device=device
    ).view(8, proposer.hidden_size)
    next_token_ids = torch.tensor([100, 200], dtype=torch.int32, device=device)

    num_rejected_tokens_gpu = torch.tensor([1, 0], dtype=torch.int32, device=device)

    num_tokens, token_indices_to_sample, output_cad = proposer.set_inputs_first_pass(
        target_token_ids=target_token_ids,
        next_token_ids=next_token_ids,
        target_positions=target_positions,
        target_hidden_states=target_hidden_states,
        token_indices_to_sample=None,
        cad=common_attn_metadata,
        num_rejected_tokens_gpu=num_rejected_tokens_gpu,
    )

    # total_output_tokens = total_input_tokens + net_num_new_slots * batch_size
    # = 8 + 2 * 2 = 12
    assert num_tokens == 12

    # Request 0: [11, 12, 100, -2, -2, 0(padding)]
    # Request 1: [21, 22, 23, 200, -2, -2]
    expected_input_ids = torch.tensor(
        [11, 12, 100, -2, -2, 0, 21, 22, 23, 200, -2, -2],
        dtype=torch.int32,
        device=device,
    )
    assert torch.equal(proposer.input_ids[:num_tokens], expected_input_ids)

    # Verify positions
    # Request 0: [5, 6, 7, 8, 9, 0 (don't care)]
    # Request 1: [10, 11, 12, 13, 14, 15]
    expected_positions = torch.tensor(
        [5, 6, 7, 8, 9, 0, 10, 11, 12, 13, 14, 15], dtype=torch.int64, device=device
    )
    assert torch.equal(
        proposer.positions[:num_tokens],
        expected_positions,
    )

    # Verify rejection mask
    expected_is_rejected = torch.zeros(12, dtype=torch.bool, device=device)
    expected_is_rejected[5] = True
    assert torch.equal(
        proposer.is_rejected_token_mask[:num_tokens], expected_is_rejected
    )

    # Verify masked token mask (parallel drafting slots should be masked)
    expected_is_masked = torch.zeros(12, dtype=torch.bool, device=device)
    expected_is_masked[3] = True
    expected_is_masked[4] = True
    expected_is_masked[10] = True
    expected_is_masked[11] = True
    assert torch.equal(proposer.is_masked_token_mask[:num_tokens], expected_is_masked)

    # Verify token_indices_to_sample (bonus + parallel drafting tokens)
    # Request 0: bonus at 2, parallel at 3, 4
    # Request 1: bonus at 9, parallel at 10, 11
    expected_token_indices_to_sample = torch.tensor(
        [2, 3, 4, 9, 10, 11], dtype=torch.int32, device=device
    )
    assert torch.equal(token_indices_to_sample, expected_token_indices_to_sample)

    # Verify the new CAD has updated query_start_loc
    # Original query_lens: [4, 4] -> Output: [6, 6]
    expected_query_start_loc = torch.tensor(
        [0, 6, 12], dtype=torch.int32, device=device
    )
    assert torch.equal(output_cad.query_start_loc, expected_query_start_loc)

    # Verify masked positions have the parallel drafting hidden state (zeros)
    parallel_drafting_hs = proposer.parallel_drafting_hidden_state_tensor
    for i in range(num_tokens):
        if expected_is_masked[i]:
            assert torch.equal(proposer.hidden_states[i], parallel_drafting_hs), (
                f"Masked position {i} should have parallel drafting hidden state"
            )