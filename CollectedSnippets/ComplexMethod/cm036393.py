def test_aborted_request_removed_from_worker_in_batch(default_vllm_config, dist_init):
    """
    Create and schedule a request so that P adds it to in-batch tracking via
    the real scheduler, then simulate an abort (request not in next scheduler
    iteration) and verify the worker no longer tracks it as in-batch.
    """
    vllm_config = create_vllm_config()

    scheduler = create_scheduler(vllm_config)
    # KVConnector Worker in P
    connector = NixlConnector(
        vllm_config, KVConnectorRole.WORKER, make_kv_cache_config(block_size=16)
    )
    connector.connector_worker = FakeNixlConnectorWorker(
        vllm_config, connector.engine_id, hand_shake_latency=0
    )

    # Create a request that triggers do_remote_decode so that
    # the scheduler adds it to reqs_in_batch
    req = create_request(request_id=1, do_remote_decode=True, max_tokens=1)
    scheduler.add_request(req)

    # First scheduling pass - examine build_connector_meta output
    sched_out = scheduler.schedule()
    kv_meta = sched_out.kv_connector_metadata
    assert kv_meta is not None
    assert isinstance(kv_meta, NixlConnectorMetadata)
    assert req.request_id in kv_meta.reqs_in_batch

    #### Model Runner start ####
    # Bind scheduler-produced metadata and start worker processing.
    connector.bind_connector_metadata(kv_meta)

    dummy_ctx = ForwardContext(
        no_compile_layers={},
        attn_metadata={},
        slot_mapping={},
    )
    connector.start_load_kv(dummy_ctx)

    # Ensure it was tracked by the worker
    assert req.request_id in connector.connector_worker._reqs_to_process

    #### Model Runner end ####

    # Abort request - request_finished call in connector scheduler
    scheduler.finish_requests(req.request_id, RequestStatus.FINISHED_ABORTED)
    # Second scheduling pass - build metadata with aborted request
    sched_out2 = scheduler.schedule()
    kv_meta2 = sched_out2.kv_connector_metadata
    assert kv_meta2 is not None
    assert isinstance(kv_meta2, NixlConnectorMetadata)
    assert req.request_id not in kv_meta2.reqs_in_batch

    # Bind empty/abort metadata and run worker step
    #### Model Runner start ####
    connector.bind_connector_metadata(kv_meta2)
    connector.start_load_kv(dummy_ctx)

    # After abort, the worker should not keep tracking it as "in-batch"
    assert req.request_id not in connector.connector_worker._reqs_to_process