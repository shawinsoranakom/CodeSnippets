def test_ec_connector_unable_to_allocate(use_kv_connector):
    """
    Test whether scheduler with ECConnector is able to handle
    unable to allocate (run out of blocks).
    """

    # Setup Scheduler With Mock External Cache Hit.
    BLOCK_SIZE = 4
    NUM_BLOCKS = 10
    scheduler = create_scheduler(
        model="llava-hf/llava-1.5-7b-hf",
        enable_prefix_caching=True,
        use_kv_connector=use_kv_connector,
        block_size=BLOCK_SIZE,
        num_blocks=NUM_BLOCKS,
        use_ec_connector=True,
        ec_role="ec_consumer",
    )

    # Mock ec_connector load external cache behavior
    scheduler.ec_connector.has_cache_item = Mock(return_value=True)
    scheduler.ec_connector.update_state_after_alloc = Mock(
        wraps=scheduler.ec_connector.update_state_after_alloc
    )

    # Create two requests. The second request will not be able to
    # allocate slots because it will not have enough blocks.
    NUM_REQUESTS = 2
    NUM_TOKENS = (NUM_BLOCKS // 2 + 1) * BLOCK_SIZE
    MAX_TOKENS = 2
    requests = create_requests(
        num_requests=NUM_REQUESTS,
        num_tokens=NUM_TOKENS,
        mm_hashes_list=[["hash_1"], ["hash_2"]],
        mm_positions=[
            [PlaceholderRange(offset=1, length=10)] for _ in range(NUM_REQUESTS)
        ],
        max_tokens=MAX_TOKENS,
        block_size=BLOCK_SIZE,
    )
    req_ids = []
    req_to_index = {}
    for i, request in enumerate(requests):
        scheduler.add_request(request)
        req_ids.append(request.request_id)
        req_to_index[request.request_id] = i

    # Setup MODEL_RUNNER_OUTPUT to be run in _step_until_done later
    MODEL_RUNNER_OUTPUT = ModelRunnerOutput(
        req_ids=req_ids,
        req_id_to_index=req_to_index,
        sampled_token_ids=[[1000]] * len(req_ids),
        logprobs=None,
        prompt_logprobs_dict={},
        pooler_output=[],
    )

    # Just one request should be running.
    output = scheduler.schedule()
    scheduled_tokens = output.num_scheduled_tokens[scheduler.running[0].request_id]
    assert scheduled_tokens == NUM_TOKENS
    assert len(scheduler.running) == 1
    assert len(scheduler.waiting) == 1

    # Should have called update_state_after_alloc for external load
    scheduler.ec_connector.update_state_after_alloc.assert_called_with(
        scheduler.running[0], 0
    )
    scheduler.ec_connector.update_state_after_alloc.reset_mock()

    # All memory should be freed, with one request waiting.
    _step_until_done(scheduler, output, MODEL_RUNNER_OUTPUT)
    assert scheduler.kv_cache_manager.block_pool.get_num_free_blocks() == NUM_BLOCKS - 1
    assert len(scheduler.running) == 0
    assert len(scheduler.waiting) == 1

    # Just one request should be running.
    output = scheduler.schedule()
    scheduled_tokens = output.num_scheduled_tokens[scheduler.running[0].request_id]
    assert scheduled_tokens == NUM_TOKENS
    assert len(scheduler.running) == 1
    assert len(scheduler.waiting) == 0

    # update_state_after_alloc should be called for loading external cache
    scheduler.ec_connector.update_state_after_alloc.assert_called_with(
        scheduler.running[0], 0
    )
    scheduler.ec_connector.update_state_after_alloc.reset_mock()

    # All memory should be freed, with no requests waiting / running.
    _step_until_done(scheduler, output, MODEL_RUNNER_OUTPUT)
    assert scheduler.kv_cache_manager.block_pool.get_num_free_blocks() == NUM_BLOCKS - 1
    assert len(scheduler.running) == 0
    assert len(scheduler.waiting) == 0