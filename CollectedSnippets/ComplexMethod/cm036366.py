def test_decode_bench_connector_basic():
    """Test basic functionality of DecodeBenchConnector."""
    block_size = 16
    num_gpu_blocks = 100

    runner = DecodeBenchTestRunner(block_size=block_size, num_gpu_blocks=num_gpu_blocks)

    # Create a request with multiple blocks worth of tokens
    num_tokens = block_size * 3  # 3 blocks
    token_ids = [1] * num_tokens

    req = runner.new_request(token_ids)

    # Run first step - should fill KV cache with dummy values
    scheduler_output, metadata = runner.run_single_step()

    # Check that get_num_new_matched_tokens returned correct value
    # Should be num_tokens - 1 (all except the last token for decode)
    expected_fill_tokens = num_tokens - 1

    # Check metadata has the request to fill
    assert len(metadata.reqs_to_fill) == 1
    assert req.request_id in metadata.reqs_to_fill

    block_ids_per_group, num_tokens_to_fill = metadata.reqs_to_fill[req.request_id]
    assert num_tokens_to_fill == expected_fill_tokens

    # For standard attention, there's only one group
    assert len(block_ids_per_group) == 1
    block_ids = block_ids_per_group[0]

    # Calculate expected number of blocks
    expected_num_blocks = (expected_fill_tokens + block_size - 1) // block_size
    assert len(block_ids) == expected_num_blocks

    # Verify KV caches were filled with constant value
    for layer_name, kv_cache in runner.kv_caches.items():
        for block_id in block_ids:
            # Check that the block was filled
            block_data = kv_cache[block_id]
            # Should be filled with constant value 0.015
            assert torch.allclose(block_data, torch.tensor(0.015))