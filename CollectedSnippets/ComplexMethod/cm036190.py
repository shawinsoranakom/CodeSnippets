def test_set_inputs_first_pass_draft_model():
    """
    Test for set_inputs_first_pass with a draft model (extra input slots,
    no shift).

    This tests the path where needs_extra_input_slots=True and
    shift_input_ids=False (draft model case). In this case:
    - Input IDs are NOT shifted
    - Each request gets extra_slots_per_request (1) new slots
    - The kernel handles copying tokens and inserting bonus/padding tokens
    - A new CommonAttentionMetadata is returned with updated query_start_loc

    Setup:
    - 2 requests
    - Request 0: tokens [10, 11, 12] at positions [0, 1, 2]
      - Only tokens [10, 11] are "valid" (query_end_loc=1),
        token 12 is a rejected token from previous speculation
    - Request 1: tokens [20, 21] at positions [0, 1], both valid.
      - Note: this is less than num_speculative_tokens (2) to ensure
        we handle variable lengths correctly.
    - next_token_ids: [100, 200] (bonus tokens)

    With extra_slots_per_request=1 and shift=False:
    Expected output layout:
    Request 0 (indices 0-3):
      - idx 0: token 10, pos 0
      - idx 1: token 11, pos 1
      - idx 2: token 100, pos 2 (bonus token)
      - idx 3: padding_token_id, is_rejected=True
    Request 1 (indices 4-6):
      - idx 4: token 20, pos 0
      - idx 5: token 21, pos 1
      - idx 6: token 200, pos 2 (bonus token)
    """
    device = torch.device(DEVICE_TYPE)

    num_speculative_tokens = 2
    block_size = BLOCK_SIZE

    # Create a proposer configured as a draft model (pass_hidden_states=False)
    # We need to mock this since _create_proposer defaults to EAGLE
    proposer = _create_proposer("draft_model", num_speculative_tokens)

    proposer.parallel_drafting_token_id = 0
    proposer.is_rejected_token_mask = torch.zeros(
        proposer.max_num_tokens, dtype=torch.bool, device=device
    )
    proposer.is_masked_token_mask = torch.zeros(
        proposer.max_num_tokens, dtype=torch.bool, device=device
    )

    # Mock draft_attn_groups to avoid needing the full model setup
    mock_kv_cache_spec = mock.MagicMock()
    mock_kv_cache_spec.block_size = block_size
    mock_attn_group = mock.MagicMock()
    mock_attn_group.kv_cache_spec = mock_kv_cache_spec
    proposer.draft_attn_groups = [mock_attn_group]

    # Request 0: query_len=3 (but 1 rejected), Request 1: query_len=2
    batch_spec = BatchSpec(
        seq_lens=[3, 2],
        query_lens=[3, 2],
    )

    common_attn_metadata = create_common_attn_metadata(
        batch_spec,
        block_size=block_size,
        device=device,
        arange_block_indices=True,  # Use predictable block indices
    )

    # Input tensors
    target_token_ids = torch.tensor(
        [10, 11, 12, 20, 21], dtype=torch.int32, device=device
    )
    target_positions = torch.tensor([0, 1, 2, 0, 1], dtype=torch.int64, device=device)
    target_hidden_states = torch.randn(
        5, proposer.hidden_size, dtype=proposer.dtype, device=device
    )
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

    assert proposer.net_num_new_slots_per_request == 1
    assert proposer.needs_extra_input_slots

    # total_output_tokens = total_input_tokens + net_num_new_slots * batch_size
    assert num_tokens == 7

    # Request 0: [10, 11, 100, padding_token (0)]
    # Request 1: [20, 21, 200]
    # Combined: [10, 11, 100, 0, 20, 21, 200]
    expected_input_ids = torch.tensor(
        [10, 11, 100, 0, 20, 21, 200], dtype=torch.int32, device=device
    )
    assert torch.equal(proposer.input_ids[:num_tokens], expected_input_ids)

    # Verify positions
    # Request 0: [0, 1, 2, 0 (don't care)]
    # Request 1: [0, 1, 2]
    # Combined: [0, 1, 2, 0, 0, 1, 2]
    expected_positions = torch.tensor(
        [0, 1, 2, 0, 0, 1, 2], dtype=torch.int64, device=device
    )
    assert torch.equal(
        proposer.positions[:num_tokens],
        expected_positions,
    )

    # Verify rejection mask
    expected_is_rejected = torch.zeros(7, dtype=torch.bool, device=device)
    expected_is_rejected[3] = True  # padding token at index 3
    assert torch.equal(
        proposer.is_rejected_token_mask[:num_tokens], expected_is_rejected
    )

    # Verify masked token mask (should all be False for non-parallel drafting)
    expected_is_masked = torch.zeros(7, dtype=torch.bool, device=device)
    assert torch.equal(proposer.is_masked_token_mask[:num_tokens], expected_is_masked)

    # Verify token_indices_to_sample (bonus tokens at indices 2 and 6)
    expected_token_indices_to_sample = torch.tensor(
        [2, 6], dtype=torch.int32, device=device
    )
    assert torch.equal(token_indices_to_sample, expected_token_indices_to_sample)

    # Verify the new CAD has updated query_start_loc
    # Original: [0, 3, 5] -> New: [0, 4, 7] (each request gains 1 slot)
    expected_query_start_loc = torch.tensor([0, 4, 7], dtype=torch.int32, device=device)
    assert torch.equal(output_cad.query_start_loc, expected_query_start_loc)