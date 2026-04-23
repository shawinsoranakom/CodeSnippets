def test_write_mode_saves_local_block_ids():
    """Write mode records local block ids in MoRIIOConnectorMetadata.reqs_to_save."""

    # Setup Scheduler and Request
    vllm_config = create_vllm_config(role="kv_producer")
    scheduler = create_scheduler(vllm_config)

    # 2 Full Blocks and 1 Half Block.
    BLOCK_SIZE = vllm_config.cache_config.block_size
    NUM_EXTERNAL_FULL_BLOCKS = 2
    NUM_TOKENS = int(BLOCK_SIZE * (NUM_EXTERNAL_FULL_BLOCKS + 0.5))

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

    # Remote Prefill, triggers MoRIIOConnectorMetadata.
    scheduler_output = scheduler.schedule()
    kv_connector_metadata = scheduler_output.kv_connector_metadata
    assert kv_connector_metadata is not None, "kv_connector_metadata is None"
    assert isinstance(kv_connector_metadata, MoRIIOConnectorMetadata)

    assert len(kv_connector_metadata.reqs_to_save) == 1, (
        "Unexpected number of reqs_to_save"
    )
    assert len(kv_connector_metadata.reqs_to_recv) == 0, (
        "Unexpected number of reqs_to_recv"
    )
    assert len(kv_connector_metadata.reqs_to_send) == 0, (
        "Unexpected number of reqs_to_send"
    )
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