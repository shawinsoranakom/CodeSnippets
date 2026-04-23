def test_transfer_failure_logging(
    default_vllm_config,
    dist_init,
    failure_type,
    wrapper_config,
    needs_get_finished,
    enable_hma,
):
    """Test that transfer failures are logged with structured context.

    Run with `pytest -sv` to see the log output.

    Covers failure types:
    - transfer_setup_failed: make_prepped_xfer fails
    - handshake_failed: add_remote_agent fails during request handshake
    - notification_failed: send_notif fails
    - transfer_failed: check_xfer_state returns bad state (e.g., "ERR")
    - transfer_exception: check_xfer_state raises exception
    """
    import logging

    vllm_config = create_vllm_config()

    connector = NixlConnector(
        vllm_config,
        KVConnectorRole.WORKER,
        make_kv_cache_config(block_size=16, swa_enabled=enable_hma),
    )
    connector.connector_worker = FakeNixlConnectorWorker(
        vllm_config,
        connector.engine_id,
        hand_shake_latency=0.0,
        kv_cache_config=connector._kv_cache_config,
    )

    # Configure FailingNixlWrapper to fail in the specified way
    for key, value in wrapper_config.items():
        setattr(connector.connector_worker.nixl_wrapper, key, value)

    request_id = f"test_{failure_type}_req"

    # For notification_failed, we need empty local blocks
    # (full cache hit path to trigger send_notif)
    local_blocks: tuple[()] | tuple[list[int], ...]
    if enable_hma:
        # HMA enabled: multiple groups (FA + SW)
        local_blocks = (
            () if failure_type == "notification_failed" else ([10, 11, 12], [13, 14])
        )
        remote_blocks = [[20, 21, 22], [23, 24]]
    else:
        # HMA disabled: single group
        local_blocks = () if failure_type == "notification_failed" else ([10, 11, 12],)
        remote_blocks = [[20, 21, 22]]

    metadata = NixlConnectorMetadata()
    metadata.add_new_req_to_recv(
        request_id=request_id,
        local_block_ids=local_blocks,
        kv_transfer_params={
            "remote_block_ids": remote_blocks,
            "remote_engine_id": FakeNixlConnectorWorker.REMOTE_ENGINE_ID,
            "remote_request_id": f"prefill-{request_id}",
            "remote_host": "localhost",
            "remote_port": 1234,
            "remote_tp_size": 1,
        },
    )
    connector.bind_connector_metadata(metadata)

    dummy_ctx = ForwardContext(
        no_compile_layers={},
        attn_metadata={},
        slot_mapping={},
    )

    # Capture logs from the nixl.worker logger specifically
    # vLLM loggers have propagate=False, so we need to capture directly
    nixl_logger = logging.getLogger(
        "vllm.distributed.kv_transfer.kv_connector.v1.nixl.worker"
    )
    captured_logs: list[logging.LogRecord] = []

    class LogCapture(logging.Handler):
        def emit(self, record):
            captured_logs.append(record)

    handler = LogCapture()
    handler.setLevel(logging.ERROR)
    nixl_logger.addHandler(handler)

    try:
        connector.start_load_kv(dummy_ctx)
        # Process the ready_requests queue (for async handshake)
        connector.bind_connector_metadata(NixlConnectorMetadata())
        # Wait for async handshake to complete
        time.sleep(0.2)
        connector.start_load_kv(dummy_ctx)

        # For transfer_failed/transfer_exception, the error happens in
        # get_finished() when checking transfer state
        if needs_get_finished:
            connector.get_finished(finished_req_ids=set())
    finally:
        nixl_logger.removeHandler(handler)

    # Print logs for manual comparison between commits
    error_logs = [r for r in captured_logs if r.levelno >= logging.ERROR]
    print("\n" + "=" * 60)
    print(f"CAPTURED ERROR LOGS for {failure_type}:")
    print("=" * 60)
    for i, record in enumerate(error_logs):
        print(f"\n--- Log {i + 1} ---")
        print(f"Message: {record.message}")
    print("=" * 60 + "\n")

    assert len(error_logs) >= 1, f"Expected at least one error log for {failure_type}"

    # Verify structured logging output (new format)
    # Check that at least one log matches the expected format
    all_messages = [r.message for r in error_logs]
    combined_logs = "\n".join(all_messages)

    assert any("NIXL transfer failure" in msg for msg in all_messages), (
        f"Expected structured log format with 'NIXL transfer failure' prefix "
        f"for {failure_type}. Got: {all_messages}"
    )
    assert any("failure_type" in msg for msg in all_messages), (
        f"Expected 'failure_type' in logs. Got: {all_messages}"
    )
    assert any("Context:" in msg for msg in all_messages), (
        f"Expected 'Context:' in logs. Got: {all_messages}"
    )
    # Check that the expected failure_type appears in at least one log
    # Note: handshake_failed also triggers handshake_setup_failed
    assert failure_type in combined_logs or (
        failure_type == "handshake_failed" and "handshake_setup_failed" in combined_logs
    ), f"Expected '{failure_type}' in logs. Got: {all_messages}"