def test_decode_bench_connector_concurrent_requests():
    """Test DecodeBenchConnector with multiple concurrent requests in the same batch."""
    block_size = 16
    num_gpu_blocks = 1000

    runner = DecodeBenchTestRunner(block_size=block_size, num_gpu_blocks=num_gpu_blocks)

    # Create multiple requests that will be batched together
    req1 = runner.new_request([1] * (block_size * 2))
    req2 = runner.new_request([2] * (block_size * 3))
    req3 = runner.new_request([3] * (block_size * 1))

    # Run first step - all requests should be filled concurrently
    _, metadata = runner.run_single_step()

    # All three requests should be in the metadata
    assert len(metadata.reqs_to_fill) == 3
    assert req1.request_id in metadata.reqs_to_fill
    assert req2.request_id in metadata.reqs_to_fill
    assert req3.request_id in metadata.reqs_to_fill

    # Verify each request has correct fill info
    block_ids_per_group1, num_tokens1 = metadata.reqs_to_fill[req1.request_id]
    block_ids_per_group2, num_tokens2 = metadata.reqs_to_fill[req2.request_id]
    block_ids_per_group3, num_tokens3 = metadata.reqs_to_fill[req3.request_id]

    # Verify token counts (all tokens except last one)
    assert num_tokens1 == block_size * 2 - 1
    assert num_tokens2 == block_size * 3 - 1
    assert num_tokens3 == block_size * 1 - 1

    # Verify block counts for each request
    assert len(block_ids_per_group1[0]) == 2  # 2 blocks
    assert len(block_ids_per_group2[0]) == 3  # 3 blocks
    assert len(block_ids_per_group3[0]) == 1  # 1 block

    # Verify all blocks are filled in KV cache
    for req_id, (block_ids_per_group, _) in metadata.reqs_to_fill.items():
        block_ids = block_ids_per_group[0]
        for layer_name, kv_cache in runner.kv_caches.items():
            for block_id in block_ids:
                block_data = kv_cache[block_id]
                assert torch.allclose(block_data, torch.tensor(0.015))

    # Run second step - should NOT fill again (already filled)
    _, metadata2 = runner.run_single_step()
    assert len(metadata2.reqs_to_fill) == 0