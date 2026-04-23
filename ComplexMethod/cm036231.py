def test_cache_key_salting():
    """
    This tests that cache salts are applied during hashing and the cache
    is separated cache as expected.
    """
    block_size = 16
    manager = KVCacheManager(
        make_kv_cache_config(block_size, 11),
        max_model_len=8192,
        enable_caching=True,
        hash_block_size=block_size,
    )

    # 3 complete blocks and an incomplete block with 11 tokens.
    common_token_ids = [i for i in range(3) for _ in range(block_size)]
    token_ids = common_token_ids + [3] * 11
    req0 = make_request("0", token_ids, block_size, sha256, cache_salt="salt1")
    computed_blocks, num_computed_tokens = manager.get_computed_blocks(req0)

    # Completed block should have hashes
    assert not computed_blocks.blocks[0]
    assert num_computed_tokens == 0
    block_hashes = req0.block_hashes
    assert len(block_hashes) == 3
    assert block_hashes[0] == sha256(
        (kv_cache_utils.NONE_HASH, tuple(token_ids[:block_size]), ("salt1",))
    )
    assert block_hashes[1] == sha256(
        (block_hashes[0], tuple(token_ids[block_size : block_size * 2]), None)
    )
    assert block_hashes[2] == sha256(
        (block_hashes[1], tuple(token_ids[block_size * 2 : block_size * 3]), None)
    )

    blocks = manager.allocate_slots(
        req0, 59, len(computed_blocks.blocks[0]) * 16, computed_blocks
    )
    assert blocks is not None
    assert blocks.get_block_ids() == ([1, 2, 3, 4],)
    req0.num_computed_tokens = 59

    # Append slots without allocating a new block.
    for _ in range(5):
        req0.append_output_token_ids(8)
    new_blocks = manager.allocate_slots(
        req0, 5, len(computed_blocks.blocks[0]) * 16, computed_blocks
    )
    assert new_blocks is not None and len(new_blocks.blocks[0]) == 0
    assert len(block_hashes) == 4
    assert block_hashes[3] == sha256(
        (block_hashes[2], tuple(token_ids[3 * block_size :] + [8] * 5), None)
    )

    # Test cache hit with a new request that has the same salt.
    token_ids = common_token_ids + [4] * 11
    req1 = make_request("1", token_ids, block_size, sha256, cache_salt="salt1")
    computed_blocks, num_computed_tokens = manager.get_computed_blocks(req1)
    # Should match only a prefix of 3 blocks.
    assert len(computed_blocks.blocks[0]) == 3
    assert num_computed_tokens == 3 * block_size

    # Test cache miss with same content but different salt.
    token_ids = common_token_ids + [4] * 11
    req2 = make_request("2", token_ids, block_size, sha256, cache_salt="salt2")
    computed_blocks, num_computed_tokens = manager.get_computed_blocks(req2)
    assert len(computed_blocks.blocks[0]) == 0
    assert num_computed_tokens == 0
    block_hashes = req2.block_hashes
    assert len(block_hashes) == 3
    assert block_hashes[0] == sha256(
        (kv_cache_utils.NONE_HASH, tuple(token_ids[:block_size]), ("salt2",))
    )
    assert block_hashes[1] == sha256(
        (block_hashes[0], tuple(token_ids[block_size : block_size * 2]), None)
    )
    assert block_hashes[2] == sha256(
        (block_hashes[1], tuple(token_ids[block_size * 2 : block_size * 3]), None)
    )