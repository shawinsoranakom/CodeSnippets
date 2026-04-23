def test_aggregate_workers_output():
    aggregator = KVOutputAggregator(expected_finished_count=2)

    output1 = DummyModelRunnerOutput()
    output2 = DummyModelRunnerOutput()

    aggregated = aggregator.aggregate([output1, output2])

    assert aggregated is output1
    aggregated = aggregated.kv_connector_output
    assert aggregated.finished_sending is None
    assert aggregated.finished_recving is None
    assert not aggregated.invalid_block_ids

    output1 = DummyModelRunnerOutput(
        finished_sending={"req1"}, finished_recving={"req2"}
    )
    output2 = DummyModelRunnerOutput(invalid_block_ids={1})

    aggregated = aggregator.aggregate([output1, output2])

    assert aggregated is output1
    aggregated = aggregated.kv_connector_output
    assert aggregated.finished_sending is None
    assert aggregated.finished_recving is None
    assert aggregated.invalid_block_ids == {1}

    output1 = DummyModelRunnerOutput(invalid_block_ids={2})
    output2 = DummyModelRunnerOutput(finished_sending={"req1"})

    aggregated = aggregator.aggregate([output1, output2])

    assert aggregated is output1
    aggregated = aggregated.kv_connector_output
    assert aggregated.finished_sending == {"req1"}
    assert aggregated.finished_recving is None
    assert aggregated.invalid_block_ids == {2}

    output1 = DummyModelRunnerOutput(invalid_block_ids={3, 4})
    output2 = DummyModelRunnerOutput(
        finished_recving={"req2"}, invalid_block_ids={4, 5}
    )

    aggregated = aggregator.aggregate([output1, output2])

    assert aggregated is output1
    aggregated = aggregated.kv_connector_output
    assert aggregated.finished_sending is None
    assert aggregated.finished_recving == {"req2"}
    assert aggregated.invalid_block_ids == {3, 4, 5}