def test_stop_via_update_from_output():
    """Test stopping behavior through update_from_output"""
    scheduler = create_scheduler(num_speculative_tokens=1)

    # Test case 1: Stop on EOS token
    requests = create_requests(num_requests=2, max_tokens=10)
    for req in requests:
        req.num_computed_tokens = req.num_tokens
        scheduler.requests[req.request_id] = req
        scheduler.running.append(req)
        req.status = RequestStatus.RUNNING

    scheduler_output = SchedulerOutput(
        scheduled_new_reqs=[],
        scheduled_cached_reqs=CachedRequestData.make_empty(),
        num_scheduled_tokens={requests[0].request_id: 1, requests[1].request_id: 2},
        total_num_scheduled_tokens=3,
        scheduled_encoder_inputs={},
        scheduled_spec_decode_tokens={
            requests[0].request_id: [],
            requests[1].request_id: [10],
        },
        num_common_prefix_blocks=[],
        finished_req_ids=set(),
        free_encoder_mm_hashes=[],
    )

    model_output = ModelRunnerOutput(
        req_ids=[req.request_id for req in requests],
        req_id_to_index={req.request_id: i for i, req in enumerate(requests)},
        sampled_token_ids=[
            [EOS_TOKEN_ID],
            [10, 11],
        ],  # First request hits EOS, second continues
        logprobs=None,
        prompt_logprobs_dict={},
        pooler_output=[],
    )

    scheduler.update_from_output(scheduler_output, model_output)

    # Verify first request stopped, second continues
    assert len(scheduler.running) == 1
    assert scheduler.running[0].request_id == requests[1].request_id
    assert requests[0].status == RequestStatus.FINISHED_STOPPED
    assert requests[0].request_id in scheduler.finished_req_ids
    assert list(requests[0].output_token_ids) == [EOS_TOKEN_ID]
    assert list(requests[1].output_token_ids) == [10, 11]

    # Test case 2: Stop on custom stop token
    scheduler = create_scheduler(num_speculative_tokens=2)
    requests = create_requests(num_requests=2, max_tokens=10, stop_token_ids=[42, 43])
    for req in requests:
        req.num_computed_tokens = req.num_tokens
        scheduler.requests[req.request_id] = req
        scheduler.running.append(req)
        req.status = RequestStatus.RUNNING

    scheduler_output = SchedulerOutput(
        scheduled_new_reqs=[],
        scheduled_cached_reqs=CachedRequestData.make_empty(),
        num_scheduled_tokens={requests[0].request_id: 3, requests[1].request_id: 2},
        total_num_scheduled_tokens=5,
        scheduled_encoder_inputs={},
        scheduled_spec_decode_tokens={
            requests[0].request_id: [10, 42],
            requests[1].request_id: [13],
        },
        num_common_prefix_blocks=[],
        finished_req_ids=set(),
        free_encoder_mm_hashes=[],
    )

    model_output = ModelRunnerOutput(
        req_ids=[req.request_id for req in requests],
        req_id_to_index={req.request_id: i for i, req in enumerate(requests)},
        sampled_token_ids=[[10, 42, 12], [13, 14]],  # First request hits stop token
        logprobs=None,
        prompt_logprobs_dict={},
        pooler_output=[],
    )

    scheduler.update_from_output(scheduler_output, model_output)

    # Verify first request stopped on custom token
    assert len(scheduler.running) == 1
    assert scheduler.running[0].request_id == requests[1].request_id
    assert requests[0].status == RequestStatus.FINISHED_STOPPED
    assert requests[0].stop_reason == 42
    assert requests[0].request_id in scheduler.finished_req_ids
    assert list(requests[0].output_token_ids) == [10, 42]
    assert list(requests[1].output_token_ids) == [13, 14]

    # Test case 3: Stop on max tokens
    scheduler = create_scheduler(num_speculative_tokens=2)
    requests = create_requests(num_requests=2, max_tokens=2)
    for req in requests:
        req.num_computed_tokens = req.num_tokens
        scheduler.requests[req.request_id] = req
        scheduler.running.append(req)
        req.status = RequestStatus.RUNNING

    scheduler_output = SchedulerOutput(
        scheduled_new_reqs=[],
        scheduled_cached_reqs=CachedRequestData.make_empty(),
        num_scheduled_tokens={requests[0].request_id: 3, requests[1].request_id: 1},
        total_num_scheduled_tokens=4,
        scheduled_encoder_inputs={},
        scheduled_spec_decode_tokens={
            requests[0].request_id: [10, 11],
            requests[1].request_id: [],
        },
        num_common_prefix_blocks=[],
        finished_req_ids=set(),
        free_encoder_mm_hashes=[],
    )

    model_output = ModelRunnerOutput(
        req_ids=[req.request_id for req in requests],
        req_id_to_index={req.request_id: i for i, req in enumerate(requests)},
        sampled_token_ids=[[10, 11, 12], [13]],  # First request exceeds max_tokens
        logprobs=None,
        prompt_logprobs_dict={},
        pooler_output=[],
    )

    scheduler.update_from_output(scheduler_output, model_output)

    # Verify first request stopped due to length
    assert len(scheduler.running) == 1
    assert scheduler.running[0].request_id == requests[1].request_id
    assert requests[0].status == RequestStatus.FINISHED_LENGTH_CAPPED
    assert requests[0].request_id in scheduler.finished_req_ids
    assert list(requests[0].output_token_ids) == [10, 11]  # Truncated to max_tokens
    assert list(requests[1].output_token_ids) == [13]

    # Test case 4: Ignore EOS flag
    scheduler = create_scheduler(num_speculative_tokens=2)
    requests = create_requests(num_requests=1, max_tokens=10, ignore_eos=True)
    requests[0].num_computed_tokens = requests[0].num_tokens
    scheduler.requests[requests[0].request_id] = requests[0]
    scheduler.running.append(requests[0])

    scheduler_output = SchedulerOutput(
        scheduled_new_reqs=[],
        scheduled_cached_reqs=CachedRequestData.make_empty(),
        num_scheduled_tokens={requests[0].request_id: 3},
        total_num_scheduled_tokens=3,
        scheduled_encoder_inputs={},
        scheduled_spec_decode_tokens={requests[0].request_id: [EOS_TOKEN_ID, 10]},
        num_common_prefix_blocks=[],
        finished_req_ids=set(),
        free_encoder_mm_hashes=[],
    )

    model_output = ModelRunnerOutput(
        req_ids=[requests[0].request_id],
        req_id_to_index={requests[0].request_id: 0},
        sampled_token_ids=[[EOS_TOKEN_ID, 10, 11]],
        logprobs=None,
        prompt_logprobs_dict={},
        pooler_output=[],
    )

    scheduler.update_from_output(scheduler_output, model_output)

    # Verify request continues past EOS
    assert len(scheduler.running) == 1
    assert not requests[0].is_finished()
    assert list(requests[0].output_token_ids) == [EOS_TOKEN_ID, 10, 11]