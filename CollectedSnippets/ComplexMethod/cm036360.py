def test_read_mode_loads_remote_block_ids(moriio_read_mode):
    """Read mode loads remote block ids into local cache mapping."""

    # Setup Scheduler and Request
    vllm_config = create_vllm_config(role="kv_consumer")
    scheduler = create_scheduler(vllm_config)

    # 2 Full Blocks and 1 Half Block.
    BLOCK_SIZE = vllm_config.cache_config.block_size
    NUM_EXTERNAL_FULL_BLOCKS = 2
    NUM_TOKENS = int(BLOCK_SIZE * (NUM_EXTERNAL_FULL_BLOCKS + 0.5))

    request = create_request(
        request_id=1,
        block_size=BLOCK_SIZE,
        num_tokens=NUM_TOKENS,
        do_remote_decode=False,
        do_remote_prefill=True,
    )
    request_id = request.request_id

    scheduler.add_request(request)
    block_list = scheduler.kv_cache_manager.coordinator.single_type_managers[
        0
    ].req_to_blocks[request_id]

    request = _setup_kv_transfer_request(request)

    # Set remote block ids to be fetched.
    request.kv_transfer_params["remote_block_ids"] = block_list

    # Remote Prefill, triggers MoRIIOConnectorMetadata.

    scheduler_output = scheduler.schedule()
    kv_connector_metadata = scheduler_output.kv_connector_metadata
    assert kv_connector_metadata is not None, "kv_connector_metadata is None"
    assert isinstance(kv_connector_metadata, MoRIIOConnectorMetadata), (
        "kv_connector_metadata is not MoRIIOConnectorMetadata"
    )
    assert len(kv_connector_metadata.reqs_to_save) == 0, (
        "Unexpected number of reqs_to_save"
    )
    assert len(kv_connector_metadata.reqs_to_recv) == 1, (
        "Unexpected number of reqs_to_recv"
    )
    assert len(kv_connector_metadata.reqs_to_send) == 0, (
        "Unexpected number of reqs_to_send"
    )
    assert request_id in kv_connector_metadata.reqs_to_recv, (
        "Request ID not in reqs_to_recv"
    )
    req_meta = kv_connector_metadata.reqs_to_recv[request_id]

    for block_id, block in zip(
        req_meta.local_block_ids,
        scheduler.kv_cache_manager.coordinator.single_type_managers[0].req_to_blocks[
            request_id
        ],
    ):
        assert block_id == block.block_id, f"{block_id} != {block.block_id}"