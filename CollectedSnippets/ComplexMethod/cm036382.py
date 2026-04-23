def test_basic_lifecycle():
    """Test lifecycle of a remote prefill."""

    vllm_config = create_vllm_config()
    scheduler = create_scheduler(vllm_config)

    # 2 Full Blocks and 1 Half Block.
    BLOCK_SIZE = vllm_config.cache_config.block_size
    NUM_EXTERNAL_FULL_BLOCKS = 2
    NUM_TOKENS = int(BLOCK_SIZE * (NUM_EXTERNAL_FULL_BLOCKS + 0.5))
    START_FREE_BLOCK_QUEUE_SIZE = (
        scheduler.kv_cache_manager.block_pool.free_block_queue.num_free_blocks
    )

    request = create_request(
        request_id=1,
        block_size=BLOCK_SIZE,
        num_tokens=NUM_TOKENS,
        do_remote_prefill=True,
    )

    scheduler.add_request(request)
    request_id = request.request_id

    # STEP (1):
    # (1a): schedule()
    scheduler_output = scheduler.schedule()

    # Nothing running and empty scheduler output.
    assert len(scheduler.running) == 0
    assert len(scheduler_output.scheduled_new_reqs) == 0
    assert scheduler_output.scheduled_cached_reqs.num_reqs == 0
    assert len(scheduler_output.num_scheduled_tokens) == 0
    assert scheduler_output.total_num_scheduled_tokens == 0

    # Req waiting for KVs with no computed/scheduled toks ...
    assert _num_waiting_requests(scheduler) == 1
    assert request in scheduler.skipped_waiting
    assert request.status == RequestStatus.WAITING_FOR_REMOTE_KVS
    assert request.num_computed_tokens == NUM_TOKENS

    # ... but should have (uncached) blocks allocated to it.
    block_pool = scheduler.kv_cache_manager.block_pool
    assert block_pool.free_block_queue.num_free_blocks < START_FREE_BLOCK_QUEUE_SIZE
    assert len(block_pool.cached_block_hash_to_block) == 0
    blocks = scheduler.kv_cache_manager.coordinator.single_type_managers[
        0
    ].req_to_blocks[request_id]
    for block in blocks:
        assert block._block_hash is None

    # (1b): forward()
    model_runner_output = EMPTY_MODEL_RUNNER_OUTPUT

    # (1c): update_from_output()
    engine_core_outputs = scheduler.update_from_output(
        scheduler_output, model_runner_output
    )
    assert not engine_core_outputs or not engine_core_outputs[0].outputs

    # STEP (2):
    # (2a): schedule(): nothing happens!
    scheduler_output = scheduler.schedule()
    assert _num_waiting_requests(scheduler) == 1
    assert len(scheduler.running) == 0

    # (2b): forward(): request finishes recv.
    model_runner_output = copy.deepcopy(EMPTY_MODEL_RUNNER_OUTPUT)
    model_runner_output.kv_connector_output = KVConnectorOutput(
        finished_recving={request_id}
    )

    # (2c): update_from_output():
    engine_core_outputs = scheduler.update_from_output(
        scheduler_output, model_runner_output
    )
    assert _num_waiting_requests(scheduler) == 1
    assert request_id in scheduler.finished_recving_kv_req_ids

    # STEP (3):
    # (3a): schedule(): this should actually schedule.
    scheduler_output = scheduler.schedule()
    assert len(scheduler.running) == 1

    # Confirm the block are actually allocated.
    num_hashed_blocks = 0
    blocks = scheduler.kv_cache_manager.coordinator.single_type_managers[
        0
    ].req_to_blocks[request_id]
    for block in blocks:
        assert block.ref_cnt == 1
        num_hashed_blocks += 1 if block._block_hash is not None else 0
    assert num_hashed_blocks == NUM_EXTERNAL_FULL_BLOCKS

    # Confirm the rest of the prompt is scheduled in this step.
    scheduled_req = scheduler_output.scheduled_new_reqs[0]
    num_scheduled_tokens = scheduler_output.num_scheduled_tokens[request_id]
    num_computed_tokens = scheduled_req.num_computed_tokens
    total_prompt_tokens = len(scheduled_req.prompt_token_ids)
    assert num_scheduled_tokens == total_prompt_tokens - num_computed_tokens

    # (3b): execute_model()
    model_runner_output = create_model_runner_output([request])
    # (3c): update_from_output()
    scheduler.update_from_output(scheduler_output, model_runner_output)

    # Step (4): Hit EOS.
    scheduler_output = scheduler.schedule()
    model_runner_output = create_model_runner_output([request], use_eos=True)
    engine_core_outputs = scheduler.update_from_output(
        scheduler_output, model_runner_output
    )
    scheduler.schedule()

    outputs = engine_core_outputs[0].outputs
    assert len(outputs) == 1
    output = outputs[0]
    assert output.finish_reason == FinishReason.STOP
    assert_scheduler_empty(scheduler)