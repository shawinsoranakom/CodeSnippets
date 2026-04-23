def test_priority_scheduling_ec_connector_preemption_and_resumption(
    cache_exist, use_kv_connector
):
    """Test that priority scheduling preempts lower priority requests
    when out of KV cache space."""
    # Create scheduler with very limited memory to force preemption
    scheduler = create_scheduler_with_priority(
        model="llava-hf/llava-1.5-7b-hf",
        enable_prefix_caching=True,
        max_num_seqs=2,  # allow multiple requests
        # kv connector should not effect test results
        use_kv_connector=use_kv_connector,
        num_blocks=15,  # can hold 244 tokens with 14 blocks (first block is null)
        block_size=16,  # standard block size
        use_ec_connector=True,
        ec_role="ec_consumer",
    )

    # Mock cache hit: Both cache exist in connector (at E->PD initially)
    scheduler.ec_connector.has_cache_item = Mock(return_value=True)
    scheduler.ec_connector.update_state_after_alloc = Mock(
        wraps=scheduler.ec_connector.update_state_after_alloc
    )

    # Create a request and schedule it (and to be preempted)
    request_low = create_requests_with_priority(
        num_requests=1,
        priorities=[1],
        arrival_times=[0.0],
        num_tokens=94,
        mm_hashes_list=[["hash_low"]],
        # NOTE: this test only preempt the last block.
        # Setting mm_position at the last block can force to recompute encoding
        mm_positions=[[PlaceholderRange(offset=82, length=10)]],
        starting_idx=0,
    )[0]
    scheduler.add_request(request_low)
    # 1st schedule
    output = scheduler.schedule()

    assert len(output.scheduled_new_reqs) == 1
    scheduled_tokens = output.num_scheduled_tokens[request_low.request_id]
    assert scheduled_tokens == 94
    assert len(scheduler.waiting) == 0
    assert len(scheduler.running) == 1

    ## Encoder-cache-specific checks:
    # Encoder cache should contain mm items from request
    _assert_right_encoder_cache_allocated(scheduler, requests=[request_low])

    # Verify update_state_after_alloc called (external load)
    scheduler.ec_connector.update_state_after_alloc.assert_called_with(request_low, 0)
    scheduler.ec_connector.update_state_after_alloc.reset_mock()

    # ECConnector should carry metadata of request
    _assert_right_ec_connector_metadata(
        output, mm_features_list=request_low.mm_features
    )

    # Scheduled encoder input should be empty; no mm to compute
    _assert_right_encoder_inputs(output, expected_total_reqs=0)

    # Simulate model execution - 1st decode
    model_output = ModelRunnerOutput(
        req_ids=[request_low.request_id],
        req_id_to_index={request_low.request_id: 0},
        sampled_token_ids=[[100]],
        # spec_token_ids=None,
        logprobs=None,
        prompt_logprobs_dict={},
        pooler_output=[],
    )
    scheduler.update_from_output(output, model_output)

    # Create a high priority request and schedule it
    request_high = create_requests_with_priority(
        num_requests=1,
        priorities=[0],
        arrival_times=[1.0],
        num_tokens=128,
        mm_hashes_list=[["hash_high"]],
        mm_positions=[[PlaceholderRange(offset=1, length=10)]],
        max_tokens=2,
        starting_idx=1,
    )[0]
    scheduler.add_request(request_high)
    # 2nd schedule
    output = scheduler.schedule()

    # KV cache should be full at this point
    assert scheduler.kv_cache_manager.block_pool.get_num_free_blocks() == 0
    assert len(output.scheduled_new_reqs) == 1
    assert output.scheduled_cached_reqs.num_reqs == 1
    assert len(scheduler.waiting) == 0
    assert len(scheduler.running) == 2

    ## Encoder-cache-specific checks:
    # Encoder cache should contain mm items from request
    _assert_right_encoder_cache_allocated(scheduler, requests=[request_high])

    # Verify update_state_after_alloc called (external load)
    scheduler.ec_connector.update_state_after_alloc.assert_called_with(request_high, 0)
    scheduler.ec_connector.update_state_after_alloc.reset_mock()

    # ECConnector should carry metadata of request
    _assert_right_ec_connector_metadata(
        output, mm_features_list=request_high.mm_features
    )

    # Scheduled encoder input should be empty; no mm to compute
    _assert_right_encoder_inputs(output, expected_total_reqs=0)

    # Simulate model execution - 2nd decode
    requests = [request_low, request_high]
    model_output = ModelRunnerOutput(
        req_ids=[req.request_id for req in requests],
        req_id_to_index={req.request_id: i for i, req in enumerate(requests)},
        sampled_token_ids=[[100] for _ in requests],
        # spec_token_ids=None,
        logprobs=None,
        prompt_logprobs_dict={},
        pooler_output=[],
    )
    scheduler.update_from_output(output, model_output)

    # 3rd schedule - - this should trigger preemption
    # req_low needs 96 tokens = 6 blocks
    # req_high needs 129 tokens = 9 blocks
    # so doesn't fit in 14 blocks.
    output = scheduler.schedule()

    # Should have preempted req_low
    assert len(output.scheduled_new_reqs) == 0
    assert output.scheduled_cached_reqs.num_reqs == 1
    assert output.scheduled_cached_reqs.req_ids[0] == request_high.request_id
    assert scheduler.requests[request_low.request_id].status == RequestStatus.PREEMPTED
    assert len(scheduler.waiting) == 1
    assert len(scheduler.running) == 1

    ## Encoder-cache-specific checks:
    # request_high is in decode phase now
    # ECConnector should carry no metadata
    _assert_right_ec_connector_metadata(output, mm_features_list=[])

    # Scheduled encoder input should be empty; no mm to compute
    _assert_right_encoder_inputs(output, expected_total_reqs=0)

    # Simulate model execution - 3rd decode, after req_low was preempted
    requests = [request_low, request_high]
    model_output = ModelRunnerOutput(
        req_ids=[req.request_id for req in requests],
        req_id_to_index={req.request_id: i for i, req in enumerate(requests)},
        sampled_token_ids=[[100], [100, 200]],
        # spec_token_ids=None,
        logprobs=None,
        prompt_logprobs_dict={},
        pooler_output=[],
    )
    # Finish the requests to make room for the preempted requests to resume
    # req_high is finished after outputting 2 tokens
    scheduler.update_from_output(output, model_output)
    scheduler.finish_requests(
        request_high.request_id, RequestStatus.FINISHED_LENGTH_CAPPED
    )

    # Set up to test different encoder cache existence scenario after preemption
    # Order of getting encoder cache should be: local cache -> connector-> compute
    # By default, the cache should still exist in local in this test case
    if cache_exist != "local":
        # Make local encoder cache empty
        scheduler.encoder_cache_manager.cached = {}

    if cache_exist == "connector_only":
        # Cache exist in ec_connector
        scheduler.ec_connector.has_cache_item = Mock(return_value=True)
    elif cache_exist == "no_where":
        scheduler.ec_connector.has_cache_item = Mock(return_value=False)

    # 4th Schedule - this should trigger req_low resumption from waiting
    output = scheduler.schedule()
    scheduled_cached_reqs = output.scheduled_cached_reqs

    assert len(output.scheduled_new_reqs) == 0
    assert scheduled_cached_reqs.num_reqs == 1
    assert len(scheduler.waiting) == 0
    assert len(scheduler.running) == 1

    # Preempted request resumed in scheduled_cached_reqs
    assert len(scheduled_cached_reqs.resumed_req_ids) == 1
    assert len(scheduled_cached_reqs.all_token_ids) == 1
    assert scheduled_cached_reqs.req_ids[0] == request_low.request_id
    assert request_low.request_id in scheduled_cached_reqs.resumed_req_ids
    assert request_low.request_id in scheduled_cached_reqs.all_token_ids
    ## Resumed tokens include 94 prompt tokens and 2 decoded tokens
    assert len(scheduled_cached_reqs.all_token_ids[request_low.request_id]) == 96
    assert scheduled_cached_reqs.all_token_ids[request_low.request_id][95] == 100
    assert scheduler.running[0].request_id == request_low.request_id
    assert request_high.request_id in output.finished_req_ids

    ## Encoder-cache-specific checks:
    # mm_hash of request_low exists in cache after scheduling for all scenario
    _assert_right_encoder_cache_allocated(scheduler, requests=[request_low])

    if cache_exist == "connector_only":
        scheduler.ec_connector.update_state_after_alloc.assert_called_with(
            request_low, 0
        )
        _assert_right_ec_connector_metadata(
            output, mm_features_list=request_low.mm_features
        )
    elif cache_exist == "local":
        scheduler.ec_connector.update_state_after_alloc.assert_not_called()
        _assert_right_ec_connector_metadata(output, mm_features_list=[])
    else:
        assert cache_exist == "no_where"
        scheduler.ec_connector.update_state_after_alloc.assert_called_with(
            request_low, 0
        )
        _assert_right_ec_connector_metadata(output, mm_features_list=[])

    scheduler.ec_connector.update_state_after_alloc.reset_mock()

    # Should only schedule encoder input when cache is not found anywhere
    if cache_exist == "no_where":
        _assert_right_encoder_inputs(
            output,
            requests=[request_low],
            expected_encoder_inputs=[[0]],
            expected_total_reqs=1,
        )
    else:
        _assert_right_encoder_inputs(output, expected_total_reqs=0)