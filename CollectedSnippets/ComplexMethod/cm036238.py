def test_different_block_size():
    block_size = 16
    # full attention and sliding window attention layers have the same page size:
    # (32 tokens/block * float16 token, vs. 16 tokens/block * float32 token)
    kv_cache_config = KVCacheConfig(
        num_blocks=100,
        kv_cache_tensors=[],
        kv_cache_groups=[
            KVCacheGroupSpec(
                ["layer1"],
                FullAttentionSpec(
                    block_size=block_size * 2,
                    num_kv_heads=1,
                    head_size=1,
                    dtype=torch.float16,
                ),
            ),
            KVCacheGroupSpec(
                ["layer2"],
                SlidingWindowSpec(
                    block_size=block_size,
                    num_kv_heads=1,
                    head_size=1,
                    dtype=torch.float32,
                    sliding_window=2 * block_size,
                ),
            ),
        ],
    )
    manager = KVCacheManager(
        kv_cache_config=kv_cache_config,
        max_model_len=8192,
        enable_caching=True,
        hash_block_size=block_size,
    )

    # 10 blocks of 16 tokens each. Token ids are not strictly aligned for each block.
    common_token_ids = [i for i in range(10) for _ in range(block_size)]

    req0 = make_request("0", common_token_ids, block_size, sha256)
    computed_blocks, num_computed_tokens = manager.get_computed_blocks(req0)
    assert not computed_blocks.blocks[0]
    assert not computed_blocks.blocks[1]
    assert num_computed_tokens == 0
    blocks = manager.allocate_slots(
        req0, 7 * block_size, len(computed_blocks.blocks[0]) * 16, computed_blocks
    )
    assert blocks.get_block_ids() == ([1, 2, 3, 4], [5, 6, 7, 8, 9, 10, 11])
    req1 = make_request("1", common_token_ids[: 7 * block_size + 1], block_size, sha256)
    computed_blocks, num_computed_tokens = manager.get_computed_blocks(req1)
    assert len(computed_blocks.blocks[0]) == 3
    assert len(computed_blocks.blocks[1]) == 6
    assert num_computed_tokens == 6 * 16

    req2 = make_request("2", common_token_ids[: 6 * block_size + 1], block_size, sha256)
    computed_blocks, num_computed_tokens = manager.get_computed_blocks(req2)
    assert len(computed_blocks.blocks[0]) == 3
    assert len(computed_blocks.blocks[1]) == 6
    assert num_computed_tokens == 6 * 16

    # Evict some blocks to make sliding window cache hit length 5*16
    # But should return 4 * 16 because full attention cache hit length must be
    # a multiple of 32
    manager.block_pool.cached_block_hash_to_block.pop(
        make_block_hash_with_group_id(req1.block_hashes[6], 1), 11
    )
    manager.block_pool.cached_block_hash_to_block.pop(
        make_block_hash_with_group_id(req1.block_hashes[5], 1), 10
    )
    computed_blocks, num_computed_tokens = manager.get_computed_blocks(req1)
    assert len(computed_blocks.blocks[0]) == 2
    assert len(computed_blocks.blocks[1]) == 4
    assert num_computed_tokens == 4 * 16