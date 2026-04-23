def test_filter_reused_manager():
    """
    Tests FilterReusedOffloadingManager with a CPUOffloadingManager.
    """
    lru_manager = CPUOffloadingManager(
        num_blocks=4, cache_policy="lru", enable_events=True
    )

    manager = FilterReusedOffloadingManager(
        backing=lru_manager, store_threshold=2, max_tracker_size=3
    )

    # Lookup [1, 2] -> 1st time, added to tracker but not eligible for store yet
    assert manager.lookup(to_key(1), _EMPTY_REQ_CTX) is False
    assert manager.lookup(to_key(2), _EMPTY_REQ_CTX) is False

    # prepare store [1, 2] -> should be filtered
    prepare_store_output = manager.prepare_store(to_keys([1, 2]), _EMPTY_REQ_CTX)
    assert prepare_store_output is not None
    assert prepare_store_output.keys_to_store == []

    # Lookup [1] -> 2nd time, eligible now
    assert manager.lookup(to_key(1), _EMPTY_REQ_CTX) is False

    # prepare store [1, 2] -> [1] should be eligible, [2] should be filtered
    prepare_store_output = manager.prepare_store(to_keys([1, 2]), _EMPTY_REQ_CTX)
    assert prepare_store_output is not None
    assert prepare_store_output.keys_to_store == to_keys([1])

    # Lookup [3, 4] -> 1st time
    # (evicts [2] from tracker since max_size is 3 and tracker has [1])
    assert manager.lookup(to_key(3), _EMPTY_REQ_CTX) is False
    assert manager.lookup(to_key(4), _EMPTY_REQ_CTX) is False
    # Verify [2] was evicted from the tracker (tracker now has: [1], [3], [4])
    assert to_keys([2])[0] not in manager.counts

    # Lookup [2] again -> (this adds [2] back to the tracker as 1st time)
    assert manager.lookup(to_key(2), _EMPTY_REQ_CTX) is False
    # Verify [2] was re-added with count=1 (not eligible yet)
    assert manager.counts.get(to_keys([2])[0]) == 1

    # prepare store [2] -> should still be filtered out since count was reset
    prepare_store_output = manager.prepare_store(to_keys([2]), _EMPTY_REQ_CTX)
    assert prepare_store_output is not None
    assert prepare_store_output.keys_to_store == []

    manager.complete_store(to_keys([1]))