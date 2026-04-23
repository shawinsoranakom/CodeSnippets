def test_maybe_evict_cached_block():
    pool = BlockPool(num_gpu_blocks=4, enable_caching=True, hash_block_size=16)
    block_hash0 = make_block_hash_with_group_id(BlockHash(b"10"), 1000)
    block_hash1 = make_block_hash_with_group_id(BlockHash(b"20"), 2000)
    block_hash2 = make_block_hash_with_group_id(BlockHash(b"30"), 3000)
    block_hashes = [
        block_hash0,
        block_hash1,
        block_hash2,
        # block3 had the exact same block_hash as the first block
        block_hash0,
    ]
    assert len(pool.blocks) == len(block_hashes)
    # Manually add all blocks to cached_blocks
    for block, block_hash in zip(pool.blocks, block_hashes):
        block.block_hash = block_hash
        pool.cached_block_hash_to_block.insert(block_hash, block)

    block0, block1, block2, block3 = pool.blocks
    assert pool.cached_block_hash_to_block._cache == {
        block_hash0: {
            block0.block_id: block0,
            block3.block_id: block3,
        },
        block_hash1: block1,
        block_hash2: block2,
    }
    # Evict block1
    pool._maybe_evict_cached_block(block1)
    assert pool.cached_block_hash_to_block._cache == {
        block_hash0: {block0.block_id: block0, block3.block_id: block3},
        block_hash2: block2,
    }
    # Evict block0: block_hash0 entry should NOT be removed, as block3
    # also use the same hash
    pool._maybe_evict_cached_block(block0)
    assert pool.cached_block_hash_to_block._cache == {
        block_hash0: {block3.block_id: block3},
        block_hash2: block2,
    }
    # Evict block2
    pool._maybe_evict_cached_block(block2)
    assert pool.cached_block_hash_to_block._cache == {block_hash0: {3: block3}}
    # Evict block3
    pool._maybe_evict_cached_block(block3)
    assert pool.cached_block_hash_to_block._cache == {}