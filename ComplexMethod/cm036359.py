def test_write_mode_with_chunked_prefill_saves_local_block_ids():
    """Write mode with chunked prefill still records correct local block ids."""
    # Setup Scheduler and Request
    MAX_NUM_BATCHED_TOKENS = 64
    NUM_TOKENS = MAX_NUM_BATCHED_TOKENS * 2 + MAX_NUM_BATCHED_TOKENS // 2

    vllm_config = create_vllm_config(
        max_num_batched_tokens=MAX_NUM_BATCHED_TOKENS, role="kv_producer"
    )
    BLOCK_SIZE = vllm_config.cache_config.block_size

    scheduler = create_scheduler(vllm_config)

    # 2 Full Blocks and 1 Half Block.

    request = create_request(
        request_id=1,
        block_size=BLOCK_SIZE,
        num_tokens=NUM_TOKENS,
        do_remote_decode=True,
        do_remote_prefill=False,
    )
    request_id = request.request_id

    scheduler.add_request(request)

    # Fake Config
    request = _setup_kv_transfer_request(request)

    # Remote Prefill with chunked prefill, triggers multiple schedules.
    expected_counts = [(0, 0, 0), (0, 0, 0), (1, 0, 0)]
    kv_connector_metadata = None
    for _, (expected_save, expected_recv, expected_send) in enumerate(expected_counts):
        scheduler_output = scheduler.schedule()
        kv_connector_metadata = scheduler_output.kv_connector_metadata

        assert len(kv_connector_metadata.reqs_to_save) == expected_save
        assert len(kv_connector_metadata.reqs_to_recv) == expected_recv
        assert len(kv_connector_metadata.reqs_to_send) == expected_send
    assert kv_connector_metadata is not None, "kv_connector_metadata is None"
    assert request_id in kv_connector_metadata.reqs_to_save, (
        "Request ID not in reqs_to_save"
    )
    req_meta = kv_connector_metadata.reqs_to_save[request_id]

    for block_id, block in zip(
        req_meta.local_block_ids,
        scheduler.kv_cache_manager.coordinator.single_type_managers[0].req_to_blocks[
            request_id
        ],
    ):
        assert block_id == block.block_id, f"{block_id} != {block.block_id}"