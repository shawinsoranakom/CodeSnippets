def test_e2e_streaming_request_update_basic_flow(mock_model_runner_with_input_batch):
    """Test that streaming session are updated correctly.

    This test validates that when a streaming session is updated with new prompt tokens:
    1. The request is removed from InputBatch before updating (avoids duplication)
    2. Request state fields are updated correctly
    3. output_token_ids is cleared (intermediate outputs are now in prompt_token_ids)
    """
    runner = mock_model_runner_with_input_batch
    req_id = "streaming_req_0"

    # Step 1: Create initial request state with some computed tokens
    initial_req_state = CachedRequestState(
        req_id=req_id,
        prompt_token_ids=[1, 2, 3],
        mm_features=[],
        sampling_params=SamplingParams(temperature=0.5),
        pooling_params=None,
        generator=None,
        block_ids=([0],),
        num_computed_tokens=3,
        output_token_ids=[10, 11],  # Generated 2 tokens
    )
    runner.requests[req_id] = initial_req_state

    # Add request to InputBatch
    runner.input_batch.add_request(initial_req_state)
    assert req_id in runner.input_batch.req_id_to_index

    # Step 2: Create new request data with extended prompt
    # The scheduler has already set prompt_token_ids to the full sequence
    # (original prompt + intermediate outputs + new prompt)
    new_req_data = Mock()
    new_req_data.prompt_token_ids = [
        1,
        2,
        3,
        10,
        4,
        5,
    ]  # Full sequence with intermediate output (10)
    new_req_data.mm_features = []
    new_req_data.prompt_embeds = None
    new_req_data.sampling_params = SamplingParams(temperature=0.8, max_tokens=50)
    new_req_data.pooling_params = None
    new_req_data.block_ids = ([0, 1],)
    new_req_data.num_computed_tokens = 4  # 3 original prompt + 1 intermediate output

    # Step 3: Update the request
    updated_req_state = GPUModelRunner._update_streaming_request(
        runner, req_id, new_req_data
    )

    # Step 4: Verify the request state was updated correctly
    assert updated_req_state.prompt_token_ids == [1, 2, 3, 10, 4, 5]
    assert updated_req_state.num_computed_tokens == 4
    assert updated_req_state.sampling_params.temperature == 0.8
    assert updated_req_state.sampling_params.max_tokens == 50
    assert updated_req_state.block_ids == ([0, 1],)

    # Verify output_token_ids were cleared
    # (intermediate outputs are now in prompt_token_ids)
    assert updated_req_state.output_token_ids == []

    # Verify the same object is returned
    assert runner.requests[req_id] is updated_req_state

    # Verify request was removed from InputBatch during update (avoids duplication)
    assert req_id not in runner.input_batch.req_id_to_index