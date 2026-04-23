def test_set_inputs_first_pass_dflash():
    """
    Test for DFlash set_inputs_first_pass.

    DFlash uses cross-attention: context tokens become K/V and only
    query tokens (bonus + mask) are Q. This tests the DFlash-specific
    input preparation where:
    - Context hidden states are stored by reference (no copy)
    - Query input_ids are [next_token, mask, mask, ...] per request
    - Context and query positions are written to separate buffers
    - token_indices_to_sample points to mask token positions only
    - A new CommonAttentionMetadata is returned with causal=False

    Setup:
    - 3 requests with query_lens [3, 2, 4]
    - num_speculative_tokens = 3
    - num_query_per_req = 4 (1 bonus + 3 mask tokens)
    - next_token_ids: [100, 200, 300]

    Expected output layout (query tokens only, 12 total):
    Request 0 (indices 0-3): [100, mask, mask, mask]
    Request 1 (indices 4-7): [200, mask, mask, mask]
    Request 2 (indices 8-11): [300, mask, mask, mask]

    Expected positions layout (separate buffers):
    Context (_context_positions_buffer, 9 tokens): copied from target_positions
    Query (positions, 12 tokens):
      Request 0: last_pos=9, query=[10, 11, 12, 13]
      Request 1: last_pos=7, query=[8, 9, 10, 11]
      Request 2: last_pos=11, query=[12, 13, 14, 15]
    """
    device = torch.device(current_platform.device_type)

    num_speculative_tokens = 3
    proposer = _create_proposer("dflash", num_speculative_tokens)
    mask_token_id = proposer.parallel_drafting_token_id

    # Setup batch with 3 requests
    batch_spec = BatchSpec(
        seq_lens=[10, 8, 12],
        query_lens=[3, 2, 4],
    )

    common_attn_metadata = create_common_attn_metadata(
        batch_spec,
        block_size=BLOCK_SIZE,
        device=device,
        arange_block_indices=True,
    )

    # Input tensors
    # Request 0: tokens [10, 11, 12] at positions [7, 8, 9]
    # Request 1: tokens [20, 21] at positions [6, 7]
    # Request 2: tokens [30, 31, 32, 33] at positions [8, 9, 10, 11]
    target_token_ids = torch.tensor(
        [10, 11, 12, 20, 21, 30, 31, 32, 33], dtype=torch.int32, device=device
    )
    target_positions = torch.tensor(
        [7, 8, 9, 6, 7, 8, 9, 10, 11], dtype=torch.int64, device=device
    )
    target_hidden_states = torch.randn(
        9, proposer.hidden_size, dtype=proposer.dtype, device=device
    )
    next_token_ids = torch.tensor([100, 200, 300], dtype=torch.int32, device=device)

    num_tokens, token_indices_to_sample, output_cad = proposer.set_inputs_first_pass(
        target_token_ids=target_token_ids,
        next_token_ids=next_token_ids,
        target_positions=target_positions,
        target_hidden_states=target_hidden_states,
        token_indices_to_sample=None,
        cad=common_attn_metadata,
        num_rejected_tokens_gpu=None,
    )

    num_query_per_req = 1 + num_speculative_tokens  # 4
    num_context = 9

    # num_tokens is the query-only count
    assert num_tokens == 3 * num_query_per_req  # 12

    # Verify input_ids (query tokens only)
    # Each request: [next_token, mask, mask, mask]
    M = mask_token_id
    expected_input_ids = torch.tensor(
        [100, M, M, M, 200, M, M, M, 300, M, M, M],
        dtype=torch.int32,
        device=device,
    )
    assert torch.equal(proposer.input_ids[:num_tokens], expected_input_ids)

    # Verify context positions (separate buffer): copied from target_positions
    assert torch.equal(
        proposer._context_positions_buffer[:num_context], target_positions
    )

    # Verify query positions (separate buffer, starts at index 0):
    # req0: last_pos=9,  query=[10, 11, 12, 13]
    # req1: last_pos=7,  query=[8, 9, 10, 11]
    # req2: last_pos=11, query=[12, 13, 14, 15]
    expected_query_positions = torch.tensor(
        [10, 11, 12, 13, 8, 9, 10, 11, 12, 13, 14, 15],
        dtype=torch.int64,
        device=device,
    )
    assert torch.equal(
        proposer.positions[:num_tokens],
        expected_query_positions,
    )

    # Verify token_indices_to_sample (mask tokens only, skip bonus at offset 0)
    # req0: query indices 0-3, mask at 1,2,3
    # req1: query indices 4-7, mask at 5,6,7
    # req2: query indices 8-11, mask at 9,10,11
    expected_token_indices_to_sample = torch.tensor(
        [1, 2, 3, 5, 6, 7, 9, 10, 11], dtype=torch.int32, device=device
    )
    assert torch.equal(token_indices_to_sample, expected_token_indices_to_sample)

    # Verify the new CAD has DFlash-specific properties
    assert output_cad.causal is False  # DFlash requires non-causal attention
    assert output_cad.num_actual_tokens == num_tokens  # query-only count
    assert output_cad.max_query_len == num_query_per_req

    expected_query_start_loc = torch.tensor(
        [0, 4, 8, 12], dtype=torch.int32, device=device
    )
    assert torch.equal(output_cad.query_start_loc, expected_query_start_loc)

    # Verify hidden states (stored by reference, not copied)
    assert proposer._dflash_hidden_states is target_hidden_states