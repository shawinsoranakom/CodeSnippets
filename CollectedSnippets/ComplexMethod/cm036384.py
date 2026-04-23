def test_no_spurious_prefix_caching():
    """
    With P/D, blocks can be allocated but uncomputed for
    multiple engine steps. This test confirms that we do
    not accidentally have cache hits against uncomputed
    blocks.
    """

    vllm_config = create_vllm_config()
    scheduler = create_scheduler(vllm_config)

    vllm_config = create_vllm_config()
    scheduler = create_scheduler(vllm_config)

    # 2 and a half full external blocks.
    BLOCK_SIZE = vllm_config.cache_config.block_size
    NUM_EXTERNAL_FULL_BLOCKS = 2
    NUM_TOKENS = int(BLOCK_SIZE * (NUM_EXTERNAL_FULL_BLOCKS + 0.5))

    # Both of these requests have prompts like [1,1,1,1,1, ...]
    request_remote = create_request(
        request_id=1,
        block_size=BLOCK_SIZE,
        num_tokens=NUM_TOKENS,
        common_prefix_len=NUM_TOKENS,
        do_remote_prefill=True,
    )

    request_local = create_request(
        request_id=2,
        block_size=BLOCK_SIZE,
        num_tokens=NUM_TOKENS,
        common_prefix_len=NUM_TOKENS,
        do_remote_prefill=False,
    )

    # Schedule the remote prefill request. This should not
    # cause any blocks to be cached.
    scheduler.add_request(request_remote)
    scheduler_output = scheduler.schedule()
    scheduler.update_from_output(scheduler_output, EMPTY_MODEL_RUNNER_OUTPUT)
    assert _num_waiting_requests(scheduler) == 1

    # Schedule the local prefill request. This should
    # cause blocks to be cached, but separately from
    scheduler.add_request(request_local)
    scheduler_output = scheduler.schedule()
    assert len(scheduler.running) == 1
    assert _num_waiting_requests(scheduler) == 1

    local_blocks = scheduler.kv_cache_manager.coordinator.single_type_managers[
        0
    ].req_to_blocks[request_local.request_id]
    remote_blocks = scheduler.kv_cache_manager.coordinator.single_type_managers[
        0
    ].req_to_blocks[request_remote.request_id]

    # Local should have cached blocks (but not all due to preallocate).
    num_hashed_blocks = 0
    for block in local_blocks:
        assert block.ref_cnt == 1
        num_hashed_blocks += 1 if block._block_hash is not None else 0
    assert num_hashed_blocks > 0

    # Remote blocks should not be cached.
    for block in remote_blocks:
        assert block.ref_cnt == 1
        assert block._block_hash is None