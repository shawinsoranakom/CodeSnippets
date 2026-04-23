def test_decode_bench_connector_large_context():
    """Test DecodeBenchConnector with large context size."""
    block_size = 16
    num_gpu_blocks = 1000

    runner = DecodeBenchTestRunner(block_size=block_size, num_gpu_blocks=num_gpu_blocks)

    # Create a request with many blocks
    num_blocks = 20
    num_tokens = block_size * num_blocks
    token_ids = list(range(num_tokens))

    req = runner.new_request(token_ids)

    # Run step
    _, metadata = runner.run_single_step()

    assert len(metadata.reqs_to_fill) == 1
    assert req.request_id in metadata.reqs_to_fill

    block_ids_per_group, num_tokens_to_fill = metadata.reqs_to_fill[req.request_id]

    # Should fill all tokens except the last one
    expected_fill_tokens = num_tokens - 1
    assert num_tokens_to_fill == expected_fill_tokens

    # For standard attention, there's only one group
    assert len(block_ids_per_group) == 1
    block_ids = block_ids_per_group[0]

    # Calculate expected number of blocks
    expected_num_blocks = (expected_fill_tokens + block_size - 1) // block_size
    assert len(block_ids) == expected_num_blocks

    # Verify blocks were filled
    for layer_name, kv_cache in runner.kv_caches.items():
        for block_id in block_ids:
            block_data = kv_cache[block_id]
            assert torch.allclose(block_data, torch.tensor(0.015))