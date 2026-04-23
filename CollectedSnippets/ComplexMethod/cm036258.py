def assert_scheduler_empty(scheduler: Scheduler):
    """Confirm the scheduler is "empty" - i.e. no leaks."""
    # Scheduler Metadata.
    assert len(scheduler.requests) == 0
    assert len(scheduler.waiting) == 0
    assert len(scheduler.running) == 0
    assert len(scheduler.finished_req_ids) == 0

    # EncoderCacheManager.
    assert len(scheduler.encoder_cache_manager.freed) == 0
    assert len(scheduler.encoder_cache_manager.cached) == 0

    # KVCache Manager.
    assert (
        len(
            scheduler.kv_cache_manager.coordinator.single_type_managers[0].req_to_blocks
        )
        == 0
    )
    assert (
        len(
            scheduler.kv_cache_manager.coordinator.single_type_managers[
                0
            ].num_cached_block
        )
        == 0
    )
    num_free_blocks = (
        scheduler.kv_cache_manager.block_pool.free_block_queue.num_free_blocks
    )
    assert num_free_blocks == (scheduler.kv_cache_manager.block_pool.num_gpu_blocks - 1)

    # NOTE(rob): just the ref count on blocks will be 0. The hash
    # value, etc will remain since we lazily evict for prefix cache.
    for block in scheduler.kv_cache_manager.block_pool.blocks:
        assert block.ref_cnt == 0