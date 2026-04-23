def test_ec_connector_schedule_multiple_requests(cache_exist, use_kv_connector):
    scheduler = create_scheduler(
        model="llava-hf/llava-1.5-7b-hf",
        max_num_seqs=10,  # allow multiple requests
        max_num_batched_tokens=2048,
        enable_prefix_caching=True,
        use_kv_connector=use_kv_connector,
        use_ec_connector=True,
        ec_role="ec_consumer",
    )
    mm_hashes_list = [[f"hash_{i}"] for i in range(10)]
    mm_positions = [[PlaceholderRange(offset=i, length=100)] for i in range(10)]
    requests = create_requests(
        num_requests=10,
        num_tokens=200,
        mm_hashes_list=mm_hashes_list,
        mm_positions=mm_positions,
    )
    for request in requests:
        scheduler.add_request(request)

    # Set up to test different encoder cache existence scenario after preemption
    # Order of getting encoder cache should be: local cache -> connector-> compute
    scheduler.ec_connector.update_state_after_alloc = Mock(
        wraps=scheduler.ec_connector.update_state_after_alloc
    )

    if cache_exist == "local":
        # Allocate cache to cache manager manually to mimic
        for req in requests:
            scheduler.encoder_cache_manager.allocate(req, 0)
    else:
        # Make sure local encoder cache empty
        scheduler.encoder_cache_manager.cached = {}

    if cache_exist == "connector_only":
        # Cache exist in ec_connector
        scheduler.ec_connector.has_cache_item = Mock(return_value=True)
    elif cache_exist == "no_where":
        scheduler.ec_connector.has_cache_item = Mock(return_value=False)

    output = scheduler.schedule()
    assert len(output.scheduled_new_reqs) == len(requests)
    assert output.scheduled_cached_reqs.num_reqs == 0
    assert len(output.finished_req_ids) == 0
    for req_id, num_tokens in output.num_scheduled_tokens.items():
        assert num_tokens == len(requests[int(req_id)].prompt_token_ids)

    ## Encoder-cache-specific checks:
    # mm_hashes of requests exist in cache after scheduling for all scenario
    _assert_right_encoder_cache_allocated(scheduler, requests=requests)

    if cache_exist == "connector_only":
        scheduler.ec_connector.update_state_after_alloc.assert_called_with(
            requests[-1], 0
        )

        # Concat mm_features for the 10 requests together
        mm_features_list = [feature for req in requests for feature in req.mm_features]

        # Check metadata should contain mm data for all 10 requests
        _assert_right_ec_connector_metadata(output, mm_features_list=mm_features_list)
    elif cache_exist == "local":
        # Local cache hit: items never reach update_state_after_alloc
        scheduler.ec_connector.update_state_after_alloc.assert_not_called()
        _assert_right_ec_connector_metadata(output, mm_features_list=[])
    else:
        # no_where: called from encoder_inputs_to_schedule but no-op
        # inside connector (has_cache_item returns False)
        assert cache_exist == "no_where"
        scheduler.ec_connector.update_state_after_alloc.assert_called()
        _assert_right_ec_connector_metadata(output, mm_features_list=[])

    scheduler.ec_connector.update_state_after_alloc.reset_mock()

    # Should only schedule encoder input when cache is not found anywhere
    if cache_exist == "no_where":
        _assert_right_encoder_inputs(
            output,
            requests=requests,
            expected_encoder_inputs=[[0] for _ in range(10)],
            expected_total_reqs=10,
        )
    else:
        _assert_right_encoder_inputs(output, expected_total_reqs=0)