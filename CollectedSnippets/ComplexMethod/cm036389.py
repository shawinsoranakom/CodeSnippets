def test_kv_connector_stats(default_vllm_config, dist_init):
    """Test that KV transfer stats are properly recorded and retrieved."""
    vllm_config = create_vllm_config()

    # Test worker role in decode server.
    connector = NixlConnector(
        vllm_config, KVConnectorRole.WORKER, make_kv_cache_config(block_size=16)
    )
    connector.connector_worker = FakeNixlConnectorWorker(
        vllm_config, connector.engine_id, hand_shake_latency=0
    )

    # Verify that xfer_stats starts empty
    initial_stats = connector.get_kv_connector_stats()
    assert initial_stats is None

    # Create transfer metadata
    request_id = "test_req_for_stats"
    metadata = NixlConnectorMetadata()
    metadata.add_new_req_to_recv(
        request_id=request_id,
        local_block_ids=([1, 2, 3],),
        kv_transfer_params={
            "remote_block_ids": ([4, 5, 6],),
            "remote_engine_id": FakeNixlConnectorWorker.REMOTE_ENGINE_ID,
            "remote_request_id": f"prefill-{request_id}",
            "remote_host": "localhost",
            "remote_port": 1234,
            "remote_tp_size": 1,
        },
    )
    connector.bind_connector_metadata(metadata)

    # Start the transfer
    dummy_ctx = ForwardContext(
        no_compile_layers={},
        attn_metadata={},
        slot_mapping={},
    )
    connector.start_load_kv(dummy_ctx)

    # Verify stats are recorded after transfer is complete
    max_iterations = 2
    # Clear metadata before start_load_kv to prevent reprocessing same request
    connector.bind_connector_metadata(NixlConnectorMetadata())
    for _ in range(max_iterations):
        # Need to call start_load_kv to process completed handshakes
        connector.start_load_kv(dummy_ctx)
        _, done_recving = connector.get_finished(finished_req_ids=set())
        if len(done_recving) > 0 and request_id in done_recving:
            break
        time.sleep(0.1)  # Small delay to allow background handshake to complete
    else:
        assert "Transfer did not complete within expected iterations"

    # Now check that stats were recorded
    stats_after_transfer = connector.get_kv_connector_stats()
    assert isinstance(stats_after_transfer, NixlKVConnectorStats)

    # Verify stats values are recorded
    assert not stats_after_transfer.is_empty()
    assert stats_after_transfer.num_successful_transfers == 1

    # Verify stats are reset after retrieval
    stats_after_reset = connector.get_kv_connector_stats()
    assert stats_after_reset is None