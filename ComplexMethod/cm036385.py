def test_full_block_prompt():
    """Test that we handle a prompt that is the full block size."""

    vllm_config = create_vllm_config()
    scheduler = create_scheduler(vllm_config)

    # 2 Full Blocks and 1 Half Block.
    BLOCK_SIZE = vllm_config.cache_config.block_size
    NUM_EXTERNAL_FULL_BLOCKS = 2
    NUM_TOKENS = int(BLOCK_SIZE * NUM_EXTERNAL_FULL_BLOCKS)

    request = create_request(
        request_id=1,
        block_size=BLOCK_SIZE,
        num_tokens=NUM_TOKENS,
        do_remote_prefill=True,
    )

    scheduler.add_request(request)
    request_id = request.request_id

    # STEP (1): Initialize a recv.
    scheduler_output = scheduler.schedule()
    # All blocks should be allocated.
    num_blocks = len(
        scheduler.kv_cache_manager.coordinator.single_type_managers[0].req_to_blocks[
            request_id
        ]
    )
    assert num_blocks == NUM_EXTERNAL_FULL_BLOCKS
    model_runner_output = EMPTY_MODEL_RUNNER_OUTPUT
    scheduler.update_from_output(scheduler_output, model_runner_output)

    # # STEP (2): Recv.
    scheduler_output = scheduler.schedule()
    model_runner_output = copy.deepcopy(EMPTY_MODEL_RUNNER_OUTPUT)
    model_runner_output.kv_connector_output = KVConnectorOutput(
        finished_recving={request_id}
    )
    scheduler.update_from_output(scheduler_output, model_runner_output)
    assert _num_waiting_requests(scheduler) == 1
    assert request_id in scheduler.finished_recving_kv_req_ids

    # # STEP (3): Run as usual.
    scheduler_output = scheduler.schedule()

    # We need to recompute the final token of the prompt to generate
    # the first new token, so we should not have a new block.
    num_blocks = len(
        scheduler.kv_cache_manager.coordinator.single_type_managers[0].req_to_blocks[
            request_id
        ]
    )
    assert num_blocks == NUM_EXTERNAL_FULL_BLOCKS
    assert scheduler_output.scheduled_new_reqs[0].num_computed_tokens == NUM_TOKENS - 1
    assert scheduler_output.num_scheduled_tokens[request_id] == 1

    model_runner_output = create_model_runner_output([request])
    scheduler.update_from_output(scheduler_output, model_runner_output)

    # # Step (4): Hit EOS.
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