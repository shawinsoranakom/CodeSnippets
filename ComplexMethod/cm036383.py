def test_interleaved_lifecycle():
    """Test Remote Prefills Work Well With Other Requests."""

    vllm_config = create_vllm_config()
    scheduler = create_scheduler(vllm_config)

    # 2 Full Blocks and 1 Half Block.
    BLOCK_SIZE = vllm_config.cache_config.block_size
    NUM_EXTERNAL_FULL_BLOCKS = 2
    NUM_TOKENS = int(BLOCK_SIZE * (NUM_EXTERNAL_FULL_BLOCKS + 0.5))

    request_remote = create_request(
        request_id=1,
        block_size=BLOCK_SIZE,
        num_tokens=NUM_TOKENS,
        do_remote_prefill=True,
    )
    request_local_a = create_request(
        request_id=2,
        block_size=BLOCK_SIZE,
        num_tokens=NUM_TOKENS,
    )
    request_local_b = create_request(
        request_id=3,
        block_size=BLOCK_SIZE,
        num_tokens=NUM_TOKENS,
    )

    # STEP 1: Regular request is running.
    scheduler.add_request(request_local_a)
    scheduler_output = scheduler.schedule()
    assert len(scheduler.running) == 1

    model_runner_output = create_model_runner_output([request_local_a])
    scheduler.update_from_output(scheduler_output, model_runner_output)

    # STEP 2: Add a local and remote request.
    scheduler.add_request(request_local_b)
    scheduler.add_request(request_remote)
    scheduler_output = scheduler.schedule()
    assert len(scheduler.running) == 2
    assert _num_waiting_requests(scheduler) == 1
    assert len(scheduler_output.scheduled_new_reqs) == 1
    assert scheduler_output.scheduled_cached_reqs.num_reqs == 1

    model_runner_output = create_model_runner_output([request_local_a, request_local_b])
    scheduler.update_from_output(scheduler_output, model_runner_output)

    # STEP 3: continue running, KVs not arrived yet.
    scheduler_output = scheduler.schedule()
    assert len(scheduler.running) == 2
    assert _num_waiting_requests(scheduler) == 1
    assert len(scheduler_output.scheduled_new_reqs) == 0
    assert scheduler_output.scheduled_cached_reqs.num_reqs == 2

    model_runner_output = create_model_runner_output(
        reqs=[request_local_a, request_local_b]
    )
    scheduler.update_from_output(scheduler_output, model_runner_output)
    assert len(scheduler.running) == 2
    assert _num_waiting_requests(scheduler) == 1
    assert len(scheduler_output.scheduled_new_reqs) == 0
    assert scheduler_output.scheduled_cached_reqs.num_reqs == 2

    # STEP 4: KVs arrive.
    scheduler_output = scheduler.schedule()
    assert len(scheduler.running) == 2
    assert _num_waiting_requests(scheduler) == 1
    assert len(scheduler_output.scheduled_new_reqs) == 0
    assert scheduler_output.scheduled_cached_reqs.num_reqs == 2

    model_runner_output = create_model_runner_output(
        [request_local_a, request_local_b], finished_recving={request_remote.request_id}
    )
    scheduler.update_from_output(scheduler_output, model_runner_output)

    # STEP 5: RECVed KVs are sent to ModelRunner.
    scheduler_output = scheduler.schedule()
    assert len(scheduler.running) == 3
    assert _num_waiting_requests(scheduler) == 0
    assert len(scheduler_output.scheduled_new_reqs) == 1
    assert scheduler_output.scheduled_cached_reqs.num_reqs == 2

    model_runner_output = create_model_runner_output(
        [request_local_a, request_local_b, request_remote]
    )
    scheduler.update_from_output(scheduler_output, model_runner_output)

    # STEP 6: Hit EOS and free.
    scheduler_output = scheduler.schedule()
    model_runner_output = create_model_runner_output(
        [request_local_a, request_local_b, request_remote],
        use_eos=True,
    )
    scheduler.update_from_output(scheduler_output, model_runner_output)
    scheduler.schedule()
    assert_scheduler_empty(scheduler)