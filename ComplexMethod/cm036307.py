def test_cpu_manager():
    """
    Tests CPUOffloadingManager with lru policy.
    """
    # initialize a CPU manager with a capacity of 4 blocks
    cpu_manager = CPUOffloadingManager(
        num_blocks=4, cache_policy="lru", enable_events=True
    )

    # prepare store [1, 2]
    prepare_store_output = cpu_manager.prepare_store(to_keys([1, 2]), _EMPTY_REQ_CTX)
    verify_store_output(
        prepare_store_output,
        ExpectedPrepareStoreOutput(
            keys_to_store=[1, 2],
            store_block_ids=[0, 1],
            evicted_keys=[],
        ),
    )

    # lookup [1, 2] -> not ready
    assert cpu_manager.lookup(to_key(1), _EMPTY_REQ_CTX) is False
    assert cpu_manager.lookup(to_key(2), _EMPTY_REQ_CTX) is False

    # no events so far
    assert list(cpu_manager.take_events()) == []

    # complete store [1, 2]
    cpu_manager.complete_store(to_keys([1, 2]))
    verify_events(cpu_manager.take_events(), expected_stores=({1, 2},))

    # lookup [1, 2]
    assert cpu_manager.lookup(to_key(1), _EMPTY_REQ_CTX) is True
    assert cpu_manager.lookup(to_key(2), _EMPTY_REQ_CTX) is True
    assert cpu_manager.lookup(to_key(3), _EMPTY_REQ_CTX) is False

    # prepare store [2, 3, 4, 5] -> evicts [1]
    prepare_store_output = cpu_manager.prepare_store(
        to_keys([2, 3, 4, 5]), _EMPTY_REQ_CTX
    )
    verify_store_output(
        prepare_store_output,
        ExpectedPrepareStoreOutput(
            keys_to_store=[3, 4, 5],
            store_block_ids=[2, 3, 0],
            evicted_keys=[1],
        ),
    )

    # verify eviction event
    verify_events(cpu_manager.take_events(), expected_evictions=({1},))

    # prepare store with no space
    assert cpu_manager.prepare_store(to_keys([1, 6]), _EMPTY_REQ_CTX) is None

    # complete store [2, 3, 4, 5]
    cpu_manager.complete_store(to_keys([2, 3, 4, 5]))

    # lookup (now that we have [2, 3, 4, 5])
    assert cpu_manager.lookup(to_key(1), _EMPTY_REQ_CTX) is False
    assert cpu_manager.lookup(to_key(2), _EMPTY_REQ_CTX) is True
    assert cpu_manager.lookup(to_key(3), _EMPTY_REQ_CTX) is True
    assert cpu_manager.lookup(to_key(4), _EMPTY_REQ_CTX) is True
    assert cpu_manager.lookup(to_key(5), _EMPTY_REQ_CTX) is True
    assert cpu_manager.lookup(to_key(0), _EMPTY_REQ_CTX) is False

    # prepare load [2, 3]
    prepare_load_output = cpu_manager.prepare_load(to_keys([2, 3]), _EMPTY_REQ_CTX)
    verify_load_output(prepare_load_output, [1, 2])

    # prepare store with no space ([2, 3] is being loaded)
    assert cpu_manager.prepare_store(to_keys([6, 7, 8]), _EMPTY_REQ_CTX) is None

    # complete load [2, 3]
    cpu_manager.complete_load(to_keys([2, 3]))

    # prepare store [6, 7, 8] -> evicts [2, 3, 4] (oldest)
    prepare_store_output = cpu_manager.prepare_store(to_keys([6, 7, 8]), _EMPTY_REQ_CTX)
    verify_store_output(
        prepare_store_output,
        ExpectedPrepareStoreOutput(
            keys_to_store=[6, 7, 8],
            store_block_ids=[3, 2, 1],
            evicted_keys=[2, 3, 4],
        ),
    )

    # complete store [6, 7, 8]
    cpu_manager.complete_store(to_keys([6, 7, 8]))

    # touch [5, 6, 7] (move to end of LRU order)
    cpu_manager.touch(to_keys([5, 6, 7]))

    # prepare store [7, 9] -> evicts [8] (oldest following previous touch)
    prepare_store_output = cpu_manager.prepare_store(to_keys([9]), _EMPTY_REQ_CTX)
    verify_store_output(
        prepare_store_output,
        ExpectedPrepareStoreOutput(
            keys_to_store=[9],
            store_block_ids=[1],
            evicted_keys=[8],
        ),
    )

    # complete store [7, 9] with failure
    cpu_manager.complete_store(to_keys([7, 9]), success=False)

    # assert [7] is still stored, but [9] is not
    assert cpu_manager.lookup(to_key(7), _EMPTY_REQ_CTX) is True
    assert cpu_manager.lookup(to_key(9), _EMPTY_REQ_CTX) is False

    verify_events(
        cpu_manager.take_events(),
        expected_stores=({3, 4, 5}, {6, 7, 8}),
        expected_evictions=({2, 3, 4}, {8}),
    )