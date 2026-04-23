def test_p_side_chunked_prefill_mamba(mock_platform):
    """P-side integration: Mamba N-1 truncation + chunked prefill completes.

    A 64-token P-side request is truncated to 63 by the N-1 fix, then
    chunked into two prefill steps (32 + 31) and finishes with
    LENGTH_CAPPED because max_tokens is set to 1.
    """
    mock_platform.device_type = "cpu"

    BATCH_SIZE = 32
    NUM_TOKENS = 64
    BLOCK_SIZE = 16

    vllm_config = create_vllm_config(
        max_num_batched_tokens=BATCH_SIZE,
        block_size=BLOCK_SIZE,
    )
    vllm_config.scheduler_config.disable_hybrid_kv_cache_manager = False

    kv_cache_config = make_kv_cache_config(
        block_size=BLOCK_SIZE,
        mamba_enabled=True,
        num_blocks=10000,
    )

    scheduler = create_scheduler(vllm_config, kv_cache_config=kv_cache_config)

    request = create_request(
        num_tokens=NUM_TOKENS,
        do_remote_decode=True,
        block_size=BLOCK_SIZE,
    )
    request.max_tokens = 128
    scheduler.add_request(request)
    request_id = request.request_id

    # ── Step 1: first chunk ──
    scheduler_output = scheduler.schedule()

    assert len(request.prompt_token_ids) == NUM_TOKENS - 1
    assert request.max_tokens == 1
    assert scheduler_output.num_scheduled_tokens[request_id] == BATCH_SIZE
    assert request.num_computed_tokens == BATCH_SIZE

    # Model returns no tokens for intermediate prefill chunk
    intermediate_output = ModelRunnerOutput(
        req_ids=[request.request_id],
        req_id_to_index={request.request_id: 0},
        sampled_token_ids=[[]],
    )
    scheduler.update_from_output(scheduler_output, intermediate_output)

    # ── Step 2: remaining chunk ──
    scheduler_output = scheduler.schedule()

    remaining = NUM_TOKENS - 1 - BATCH_SIZE  # 31
    assert scheduler_output.num_scheduled_tokens[request_id] == remaining
    assert request.num_computed_tokens == NUM_TOKENS - 1

    # Prefill complete: model generates 1 decode token
    final_output = create_model_runner_output([request])
    engine_core_outputs = scheduler.update_from_output(scheduler_output, final_output)

    # max_tokens=1 → request finishes with LENGTH
    outputs = engine_core_outputs[0].outputs
    assert len(outputs) == 1
    assert outputs[0].finish_reason == FinishReason.LENGTH