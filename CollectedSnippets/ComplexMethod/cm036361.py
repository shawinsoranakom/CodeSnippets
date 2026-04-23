def test_connector_receives_block_hashes(_load_plugin):
    block_size = 16
    num_tokens = 48  # 3 full blocks worth of tokens
    scheduler = create_scheduler(
        use_kv_connector="DummyKVConnector", block_size=block_size
    )
    requests = create_requests(
        num_requests=3, num_tokens=num_tokens, block_size=block_size
    )
    for req in requests:
        scheduler.add_request(req)

    output = scheduler.schedule()

    # Verify the connector metadata was built with block hashes.
    meta = output.kv_connector_metadata
    assert isinstance(meta, DummyConnectorMetadata)
    assert len(meta.block_hashes_by_req) == 3

    for req in requests:
        assert req.request_id in meta.block_hashes_by_req
        # Each request has num_tokens / block_size = 3 full block hashes.
        assert len(meta.block_hashes_by_req[req.request_id]) == (
            num_tokens // block_size
        )
        assert meta.block_hashes_by_req[req.request_id] == req.block_hashes