def test_cache_blocks_multi_group():
    """
    This tests that blocks are cached correctly for different kv cache groups.
    """
    block_size = 4
    block_pool = BlockPool(
        num_gpu_blocks=10, enable_caching=True, hash_block_size=block_size
    )

    # Req:
    #  Block 0/4: [0, 1, 2, 3]
    #  Block 1/5: [4, 5, 6, 7]
    #  Block 2/6: [8, 9, 10, 11]
    #  Block 3/7: [12, 13]
    req = make_request("0", list(range(14)), block_size, sha256)

    # Cache the blocks for group 0.
    blocks = [KVCacheBlock(block_id=i) for i in range(2)]
    block_pool.cache_full_blocks(
        request=req,
        blocks=blocks,
        num_cached_blocks=0,
        num_full_blocks=2,
        block_size=block_size,
        kv_cache_group_id=0,
    )
    assert len(block_pool.cached_block_hash_to_block) == 2
    assert len(req.block_hashes) == 3
    assert all([block.block_hash is not None for block in blocks])

    # Cache the blocks for group 1.
    blocks = [KVCacheBlock(block_id=i) for i in range(3)]
    block_pool.cache_full_blocks(
        request=req,
        blocks=blocks,
        num_cached_blocks=0,
        num_full_blocks=3,
        block_size=block_size,
        kv_cache_group_id=1,
    )
    assert len(block_pool.cached_block_hash_to_block) == 5
    assert len(req.block_hashes) == 3
    assert all([block.block_hash is not None for block in blocks])

    # Block hash 0: hit for group 0 and 1
    # Block hash 1: hit for group 0 and 1
    # Block hash 2: hit for group 1

    assert (
        block_pool.get_cached_block(req.block_hashes[0], kv_cache_group_ids=[0])
        is not None
    )
    assert (
        block_pool.get_cached_block(req.block_hashes[1], kv_cache_group_ids=[0])
        is not None
    )
    assert (
        block_pool.get_cached_block(req.block_hashes[2], kv_cache_group_ids=[0]) is None
    )
    assert (
        block_pool.get_cached_block(req.block_hashes[0], kv_cache_group_ids=[1])
        is not None
    )
    assert (
        block_pool.get_cached_block(req.block_hashes[1], kv_cache_group_ids=[1])
        is not None
    )
    assert (
        block_pool.get_cached_block(req.block_hashes[2], kv_cache_group_ids=[1])
        is not None
    )
    assert (
        block_pool.get_cached_block(req.block_hashes[0], kv_cache_group_ids=[0, 1])
        is not None
    )
    assert (
        block_pool.get_cached_block(req.block_hashes[1], kv_cache_group_ids=[0, 1])
        is not None
    )
    assert (
        block_pool.get_cached_block(req.block_hashes[2], kv_cache_group_ids=[0, 1])
        is None
    )