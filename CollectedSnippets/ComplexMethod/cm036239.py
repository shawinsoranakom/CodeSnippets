def test_block_lookup_cache_single_block_per_key():
    cache = BlockHashToBlockMap()
    key0 = BlockHashWithGroupId(b"hash0")
    key1 = BlockHashWithGroupId(b"hash1")
    key2 = BlockHashWithGroupId(b"hash2")
    block0 = KVCacheBlock(0)
    block1 = KVCacheBlock(1)

    assert cache.get_one_block(key0) is None
    assert cache.get_one_block(key1) is None
    assert cache.get_one_block(key2) is None
    # key0 inserted
    cache.insert(key0, block0)
    assert cache.get_one_block(key0) is block0
    assert cache.get_one_block(key1) is None
    assert cache.get_one_block(key2) is None
    # key1 inserted
    cache.insert(key1, block1)
    assert cache.get_one_block(key0) is block0
    assert cache.get_one_block(key1) is block1
    assert cache.get_one_block(key2) is None
    # No block popped due to block_id mismatch
    assert cache.pop(key0, 100) is None
    assert cache.get_one_block(key0) is block0
    assert cache.get_one_block(key1) is block1
    assert cache.get_one_block(key2) is None
    # block popped with (key0, block ID 0)
    assert cache.pop(key0, 0) is block0
    assert cache.get_one_block(key0) is None
    assert cache.get_one_block(key1) is block1
    assert cache.get_one_block(key2) is None
    # No block popped due to block_id mismatch
    assert cache.pop(key0, 1) is None
    assert cache.get_one_block(key0) is None
    assert cache.get_one_block(key1) is block1
    assert cache.get_one_block(key2) is None
    # block popped with (key1, block ID 1)
    assert cache.pop(key1, 1) is block1
    assert cache.get_one_block(key0) is None
    assert cache.get_one_block(key1) is None
    assert cache.get_one_block(key2) is None