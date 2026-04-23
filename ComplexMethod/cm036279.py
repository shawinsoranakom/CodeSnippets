def test_prefix_caching_for_prefill_dedup():
    CHUNK_SIZE = 1000
    BLOCK_SIZE = 16
    num_prompt_tokens = 100
    scheduler = create_scheduler(
        async_scheduling=True,
        max_num_batched_tokens=CHUNK_SIZE,
        enable_prefix_caching=True,
        block_size=BLOCK_SIZE,
    )
    requests = create_requests(
        num_requests=5,
        num_tokens=num_prompt_tokens,
        max_tokens=3,
        same_prompt=True,
        block_size=BLOCK_SIZE,
    )

    # Two requests with the same prompt.
    req0 = requests.pop(0)
    req1 = requests.pop(0)
    scheduler.add_request(req0)
    scheduler.add_request(req1)

    sched_outputs: deque[SchedulerOutput] = deque()
    sched_output = scheduler.schedule()
    sched_outputs.append(sched_output)
    # Make sure prefix caching de-duplicates the prompts in the same step,
    # so all the blocks except the last are shared between the two requests.
    assert len(sched_output.num_scheduled_tokens) == 2
    assert sched_output.num_scheduled_tokens[req0.request_id] == num_prompt_tokens
    assert (
        sched_output.num_scheduled_tokens[req1.request_id]
        == num_prompt_tokens % BLOCK_SIZE
    )

    sched_outputs.append(scheduler.schedule())
    while sched_outputs:
        added_req = None
        if requests:
            added_req = requests.pop(0)
            scheduler.add_request(added_req)
        sched_output = sched_outputs.popleft()
        model_runner_output = _make_model_runner_output(sched_output)
        scheduler.update_from_output(sched_output, model_runner_output)
        sched_output = scheduler.schedule()
        if sched_output.num_scheduled_tokens:
            sched_outputs.append(sched_output)
            if added_req:
                assert (
                    sched_output.num_scheduled_tokens[added_req.request_id]
                    == num_prompt_tokens % BLOCK_SIZE
                )

    assert scheduler.get_num_unfinished_requests() == 0