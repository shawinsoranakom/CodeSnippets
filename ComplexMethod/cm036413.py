def test_e2e_streaming_request_update_basic_flow(
    mock_model_runner_with_req_states,
):
    """Test that streaming sessions are updated correctly.

    This test validates that when a streaming session is updated with new
    prompt tokens:
    1. The old request state is removed (no free_indices leak)
    2. The new state is written with updated prefill_token_ids
    3. model_state and block_tables are re-registered for the new state
    """
    runner = mock_model_runner_with_req_states
    req_states = runner.req_states
    req_id = "streaming_req_0"
    initial_free = len(req_states.free_indices)

    # Step 1: Add initial request with 3 prompt tokens, all computed
    initial_req_data = NewRequestData(
        req_id=req_id,
        prompt_token_ids=[1, 2, 3],
        prefill_token_ids=[1, 2, 3],
        mm_features=[],
        sampling_params=None,
        pooling_params=None,
        block_ids=([0],),
        num_computed_tokens=3,
        lora_request=None,
    )
    runner.add_requests(_make_scheduler_output([initial_req_data]))
    assert req_id in req_states.req_id_to_index
    assert len(req_states.free_indices) == initial_free - 1

    # Step 2: Create streaming update with extended prompt
    # The scheduler has already set prefill_token_ids to the full sequence
    # (original prompt + intermediate output + new prompt tokens)
    updated_req_data = NewRequestData(
        req_id=req_id,
        prompt_token_ids=[1, 2, 3],
        prefill_token_ids=[1, 2, 3, 10, 4, 5],
        mm_features=[],
        sampling_params=None,
        pooling_params=None,
        block_ids=([0, 1],),
        num_computed_tokens=4,  # 3 original prompt + 1 intermediate output
        lora_request=None,
    )
    runner.add_requests(_make_scheduler_output([updated_req_data]))

    # Step 3: Verify no free_indices leak (old slot recycled)
    assert len(req_states.free_indices) == initial_free - 1

    # Verify the request is still tracked with exactly one index
    assert req_id in req_states.req_id_to_index
    assert sum(1 for v in req_states.index_to_req_id.values() if v == req_id) == 1

    # Verify state was updated with new values
    new_idx = req_states.req_id_to_index[req_id]
    assert req_states.prompt_len.np[new_idx] == 3
    assert req_states.prefill_len.np[new_idx] == 6
    assert req_states.num_computed_prefill_tokens[new_idx] == 4

    # Verify model_state and block_tables were re-registered
    runner.model_state.add_request.assert_called_with(new_idx, updated_req_data)
    runner.block_tables.append_block_ids.assert_called_with(
        new_idx, ([0, 1],), overwrite=True
    )