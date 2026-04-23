def test_kv_cache_events(blocks_to_cache: int):
    block_size = 16
    num_blocks = blocks_to_cache + 1

    # Allocate Blocks
    # Should see a single block stored event with a blocks_to_cache number of
    # block hashes
    # take_events should reset the kv_event_queue
    manager = KVCacheManager(
        make_kv_cache_config(block_size, num_blocks),
        max_model_len=8192,
        enable_caching=True,
        enable_kv_cache_events=True,
        hash_block_size=block_size,
    )

    num_tokens = block_size * blocks_to_cache
    req0 = make_request("0", list(range(num_tokens)), block_size, sha256)
    _ = manager.allocate_slots(req0, num_tokens)
    events = manager.take_events()

    block = events[-1]
    assert (
        len(block.block_hashes)
        == blocks_to_cache
        == len(manager.block_pool.cached_block_hash_to_block)
    )
    assert len(block.token_ids) == block.block_size * len(block.block_hashes)
    assert len(manager.block_pool.kv_event_queue) == 0

    stored_block_hash = block.block_hashes

    # Remove blocks and send another request
    # Should see block_to_cache number of removed block events and a new block
    # stored event
    manager.free(req0)
    req1 = make_request("1", list(range(num_tokens)), block_size, sha256)
    _ = manager.allocate_slots(req1, num_tokens)
    events = manager.take_events()

    for blocks in events[:-1]:
        assert blocks.block_hashes[0] in stored_block_hash
    assert len(events) == blocks_to_cache + 1
    assert isinstance(events[-2], BlockRemoved)
    assert (
        len(events[-1].block_hashes)
        == blocks_to_cache
        == len(manager.block_pool.cached_block_hash_to_block)
    )

    # All Blocks Cleared
    # Should see a single all blocks cleared event
    manager.free(req1)
    manager.reset_prefix_cache()
    events = manager.take_events()

    assert isinstance(events[-1], AllBlocksCleared)
    assert len(manager.block_pool.cached_block_hash_to_block) == 0