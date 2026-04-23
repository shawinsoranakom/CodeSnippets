def test_cannot_schedule_after_recv():
    """
    Test that we can handle no schedule after recv due to not
    enough remaining KV blocks.
    """

    # NOTE: the KVCacheManager will use 1 null block.
    # So there are 5 total working blocks.
    TOTAL_NUM_BLOCKS = 6
    vllm_config = create_vllm_config()
    scheduler = create_scheduler(vllm_config, num_blocks=TOTAL_NUM_BLOCKS)

    # Prime the KVCache.
    NUM_PROMPT_BLOCKS = 2
    BLOCK_SIZE = vllm_config.cache_config.block_size
    # Prompt will use 2 blocks + 1 block after we schedule.
    NUM_TOKENS_LOCAL = int(BLOCK_SIZE * NUM_PROMPT_BLOCKS)
    NUM_TOKENS_REMOTE = int(BLOCK_SIZE * NUM_PROMPT_BLOCKS)

    request_normal = create_request(
        request_id=1, block_size=BLOCK_SIZE, num_tokens=NUM_TOKENS_LOCAL
    )
    request_remote = create_request(
        request_id=2,
        block_size=BLOCK_SIZE,
        num_tokens=NUM_TOKENS_REMOTE,
        do_remote_prefill=True,
    )

    # STEP 1: 3 blocks are in use (2 for prompt, 1 for decode).
    scheduler.add_request(request_normal)
    scheduler_output = scheduler.schedule()
    model_runner_output = create_model_runner_output(reqs=[request_normal])
    scheduler.update_from_output(scheduler_output, model_runner_output)
    assert len(scheduler.running) == 1
    assert _num_waiting_requests(scheduler) == 0

    # Step 2: 5 blocks are in use (2 new for remote blocks).
    scheduler.add_request(request_remote)
    scheduler_output = scheduler.schedule()
    model_runner_output = create_model_runner_output(reqs=[request_normal])
    scheduler.update_from_output(scheduler_output, model_runner_output)
    assert len(scheduler.running) == 1
    assert _num_waiting_requests(scheduler) == 1

    # Step 3: finish recving (5 blocks in use)
    scheduler_output = scheduler.schedule()
    model_runner_output = create_model_runner_output(
        reqs=[request_normal], finished_recving={request_remote.request_id}
    )
    scheduler.update_from_output(scheduler_output, model_runner_output)
    assert len(scheduler.running) == 1
    assert _num_waiting_requests(scheduler) == 1

    # Step 4: try to schedule, remote request is put to running list
    # because the transfer is completed.
    scheduler_output = scheduler.schedule()
    model_runner_output = create_model_runner_output(
        reqs=[request_normal, request_remote]
    )
    scheduler.update_from_output(scheduler_output, model_runner_output)
    assert len(scheduler.running) == 2
    assert _num_waiting_requests(scheduler) == 0

    # Step 5: Remote request will be put back to waiting list
    # because it needs new block to hold generated token.
    scheduler_output = scheduler.schedule()
    model_runner_output = create_model_runner_output(reqs=[request_normal])
    scheduler.update_from_output(scheduler_output, model_runner_output)
    assert len(scheduler.running) == 1
    assert _num_waiting_requests(scheduler) == 1

    # Step 6: finish the request, free it.
    scheduler_output = scheduler.schedule()
    model_runner_output = create_model_runner_output(
        reqs=[request_normal], use_eos=True
    )
    scheduler.update_from_output(scheduler_output, model_runner_output)
    assert len(scheduler.running) == 0
    assert _num_waiting_requests(scheduler) == 1

    # Step 7: now we can schedule (with 2 blocks computed),
    # request is retrieved from preempted list.
    scheduler_output = scheduler.schedule()
    model_runner_output = create_model_runner_output(reqs=[request_remote])
    assert (
        scheduler_output.scheduled_cached_reqs.num_computed_tokens[0]
        == NUM_PROMPT_BLOCKS * BLOCK_SIZE
    )
    scheduler.update_from_output(scheduler_output, model_runner_output)
    assert len(scheduler.running) == 1
    assert _num_waiting_requests(scheduler) == 0

    # Step 8: free everything.
    scheduler_output = scheduler.schedule()
    model_runner_output = create_model_runner_output(
        reqs=[request_remote], use_eos=True
    )
    scheduler.update_from_output(scheduler_output, model_runner_output)
    _ = scheduler.schedule()
    assert_scheduler_empty(scheduler)