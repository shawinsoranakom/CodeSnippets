def test_offloading_connector(request_runner, async_scheduling: bool):
    offloaded_block_size = 12
    gpu_block_size = 4
    num_gpu_blocks = 100
    block_size_factor = offloaded_block_size // gpu_block_size

    runner = request_runner(
        offloaded_block_size=offloaded_block_size,
        gpu_block_size=gpu_block_size,
        num_gpu_blocks=num_gpu_blocks,
        async_scheduling=async_scheduling,
    )

    # 3 blocks, store just the middle block (skip first and last)
    # blocks = [0, 1, 2], [3, 4, 5], [6, 7, 8]
    runner.new_request(token_ids=[0] * offloaded_block_size * 3)
    runner.manager.prepare_store.side_effect = (
        lambda keys, req_context: generate_store_output(list(keys)[1:2])
    )
    runner.run(decoded_tokens=[0])

    # add block missing 1 token -> no offload
    runner.run(
        decoded_tokens=[0] * (offloaded_block_size - 1),
        expected_stored_gpu_block_indexes=(3, 4, 5),
    )
    runner.manager.prepare_store.assert_not_called()

    # +1 token -> single block, fail prepare_store
    runner.manager.prepare_store.side_effect = lambda keys, req_context: None
    runner.run(decoded_tokens=[0])
    runner.manager.prepare_store.assert_called()

    # 1 more block (+ token for async scheduling)
    # now set block_hashes_to_store = []
    runner.manager.prepare_store.side_effect = (
        lambda keys, req_context: generate_store_output([])
    )
    runner.run(decoded_tokens=[0] * (offloaded_block_size + 1))

    # 1 more block (+ token for kicking off offloading)
    # now check touch was called with all 6 blocks
    runner.manager.prepare_store.side_effect = (
        lambda keys, req_context: generate_store_output(keys)
    )
    runner.run(
        decoded_tokens=[0] * (offloaded_block_size + 1),
        expected_stored_gpu_block_indexes=(15, 16, 17),
    )
    runner.manager.touch.assert_called()
    block_hashes1 = list(runner.manager.touch.call_args.args[0])
    assert len(block_hashes1) == 6

    # terminate request
    runner.run(decoded_tokens=[EOS_TOKEN_ID])

    # create a new request differing only on the last token
    runner.new_request(token_ids=[0] * (offloaded_block_size * 6 - 1) + [1])
    runner.run(decoded_tokens=[0])
    runner.manager.touch.assert_called()
    block_hashes2 = list(runner.manager.touch.call_args.args[0])
    assert len(block_hashes2) == 6

    # verify hashes are the same, except for the last block
    assert block_hashes1[:5] == block_hashes2[:5]
    assert block_hashes1[5] != block_hashes2[5]

    # terminate request
    runner.run(
        decoded_tokens=[EOS_TOKEN_ID],
        expected_stored_gpu_block_indexes=tuple(range(6 * block_size_factor)),
    )

    # full_block_tokens - num_computed_tokens < offloaded_block_size
    runner.new_request(
        token_ids=[0] * gpu_block_size + [1] * (offloaded_block_size - gpu_block_size)
    )
    runner.manager.prepare_store.side_effect = (
        lambda keys, req_context: generate_store_output([])
    )
    runner.run(decoded_tokens=[EOS_TOKEN_ID])
    runner.manager.lookup.assert_not_called()

    # single block lookup with no hits
    runner.new_request(token_ids=[1] * offloaded_block_size)
    runner.manager.prepare_store.side_effect = (
        lambda keys, req_context: generate_store_output([])
    )
    runner.run(decoded_tokens=[EOS_TOKEN_ID])
    runner.manager.lookup.assert_called_once()

    # single block lookup with a hit
    runner.scheduler.reset_prefix_cache()
    runner.new_request(token_ids=[0] * offloaded_block_size)
    runner.manager.prepare_store.side_effect = (
        lambda keys, req_context: generate_store_output([])
    )
    runner.connector_scheduler._maximal_prefix_lookup = lambda key, req_context: 1
    runner.run(
        decoded_tokens=[EOS_TOKEN_ID], expected_loaded_gpu_block_indexes=(0, 1, 2)
    )

    # single block lookup with a hit in a middle block
    runner.new_request(
        token_ids=[0] * offloaded_block_size * 2 + [1] * offloaded_block_size
    )
    runner.manager.prepare_store.side_effect = (
        lambda keys, req_context: generate_store_output([])
    )
    runner.connector_scheduler._maximal_prefix_lookup = lambda key, req_context: 1
    runner.run(
        decoded_tokens=[EOS_TOKEN_ID], expected_loaded_gpu_block_indexes=(3, 4, 5)
    )

    # test take_events
    def to_hashes(int_hashes: list[int]) -> list[BlockHash]:
        return [BlockHash(str(i).encode()) for i in int_hashes]

    def take_events() -> Iterable[OffloadingEvent]:
        yield OffloadingEvent(keys=to_keys([1, 2, 3]), medium="A", removed=False)
        yield OffloadingEvent(keys=to_keys([4, 5, 6]), medium="B", removed=True)

    runner.manager.take_events.side_effect = take_events
    events = list(runner.scheduler_connector.take_events())
    assert len(events) == 2
    event = events[0]
    assert isinstance(event, BlockStored)
    assert event.block_hashes == to_hashes([1, 2, 3])
    assert event.block_size == 0
    assert event.medium == "A"
    assert event.token_ids == []
    assert event.parent_block_hash is None
    assert event.lora_id is None
    assert event.lora_name is None
    event = events[1]
    assert isinstance(event, BlockRemoved)
    assert event.block_hashes == to_hashes([4, 5, 6])
    assert event.medium == "B"