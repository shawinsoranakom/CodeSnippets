def test_external_prefix_cache_metrics(is_async: bool, local_cache_hits: bool):
    """
    Verify connector prefix cache metrics are updated
    correctly when the scheduler processes requests with KV connector hits.
    """

    BLOCK_SIZE = 16
    if local_cache_hits:
        NUM_MATCHED_NEW_TOKENS = BLOCK_SIZE * 2  # 32 tokens
        NUM_LOCAL_HITS = NUM_MATCHED_NEW_TOKENS * 2  # 64 tokens
        NUM_REQUESTS = 1
        NUM_TOKENS = NUM_LOCAL_HITS * 2  # 128 tokens
    else:
        NUM_MATCHED_NEW_TOKENS = 4
        NUM_LOCAL_HITS = 0
        NUM_REQUESTS = 2
        NUM_TOKENS = 8  # 8 tokens

    # Setup Scheduler.
    scheduler = create_scheduler(
        enable_prefix_caching=local_cache_hits,
        use_kv_connector=mock_kv(
            matched_tokens=NUM_MATCHED_NEW_TOKENS, is_async=is_async
        ),
        block_size=BLOCK_SIZE,
    )

    if local_cache_hits:
        # First, establish local cache by running a request to completion
        requests = create_requests(
            num_requests=1,
            num_tokens=NUM_LOCAL_HITS,
            max_tokens=2,
            block_size=BLOCK_SIZE,
        )
        req_ids = []
        req_to_index = {}
        for i, request in enumerate(requests):
            scheduler.add_request(request)
            req_ids.append(request.request_id)
            req_to_index[request.request_id] = i

        if is_async:
            _step_until_kv_transfer_finished(scheduler, req_ids)

        # Run first request to completion to establish local cache
        output = scheduler.schedule()
        MODEL_RUNNER_OUTPUT = ModelRunnerOutput(
            req_ids=req_ids,
            req_id_to_index=req_to_index,
            sampled_token_ids=[[1000]] * len(req_ids),
            logprobs=None,
            prompt_logprobs_dict={},
            pooler_output=[],
        )
        _step_until_done(scheduler, output, MODEL_RUNNER_OUTPUT)
        _ = scheduler.schedule()

    # --- Prepare test requests ---
    MAX_TOKENS = 2
    requests = create_requests(
        num_requests=NUM_REQUESTS,
        num_tokens=NUM_TOKENS,
        max_tokens=MAX_TOKENS,
        block_size=BLOCK_SIZE,
    )
    req_ids = []
    req_to_index = {}
    for i, request in enumerate(requests):
        scheduler.add_request(request)
        req_ids.append(request.request_id)
        req_to_index[request.request_id] = i

    initial_ecos = None
    if is_async:
        initial_ecos = _step_until_kv_transfer_finished(scheduler, req_ids)

    # --- Trigger scheduling and simulate model output ---
    output = scheduler.schedule()
    MODEL_RUNNER_OUTPUT = ModelRunnerOutput(
        req_ids=[r.request_id for r in requests],
        req_id_to_index={r.request_id: i for i, r in enumerate(requests)},
        sampled_token_ids=[[1000]] * NUM_REQUESTS,
        logprobs=None,
        prompt_logprobs_dict={},
        pooler_output=[],
    )

    # Update scheduler stats
    ecos = scheduler.update_from_output(output, MODEL_RUNNER_OUTPUT)

    # --- Assertions ---
    assert ecos is not None and len(ecos) > 0
    assert ecos[0].scheduler_stats is not None

    if local_cache_hits:
        # For async, local cache stats come from the first step
        if initial_ecos:
            local_stats = initial_ecos[0].scheduler_stats.prefix_cache_stats
        else:
            local_stats = ecos[0].scheduler_stats.prefix_cache_stats
        assert local_stats is not None
        assert local_stats.queries == NUM_TOKENS * NUM_REQUESTS
        assert local_stats.hits == NUM_LOCAL_HITS * NUM_REQUESTS

    if initial_ecos:
        external_stats = initial_ecos[0].scheduler_stats.connector_prefix_cache_stats
    else:
        external_stats = ecos[0].scheduler_stats.connector_prefix_cache_stats
    assert external_stats is not None

    assert external_stats.queries == (NUM_TOKENS - NUM_LOCAL_HITS) * NUM_REQUESTS
    assert external_stats.hits == NUM_MATCHED_NEW_TOKENS * NUM_REQUESTS
    assert external_stats.requests == NUM_REQUESTS
    assert external_stats.preempted_requests == 0