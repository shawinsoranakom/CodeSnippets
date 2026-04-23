def test_kv_connector_stats_aggregation():
    """
    Test KV transfer stats aggregation across TP ranks using
    KVOutputAggregator (used by MultiprocExecutor).
    """

    # Create KVOutputAggregator for 3 workers (simulating TP=3), same thing
    # done in MultiprocExecutor.execute_model
    aggregator = KVOutputAggregator(expected_finished_count=3)

    # Create stats for multiple workers with different transfer patterns
    worker1_stats = NixlKVConnectorStats()
    worker2_stats = NixlKVConnectorStats()
    worker3_stats = NixlKVConnectorStats()

    # Record different transfers on each worker
    # Worker 1: 2 transfers
    stats = get_default_xfer_telemetry()
    worker1_stats.record_transfer(stats)
    worker1_stats.record_transfer(stats)

    # Worker 2: 1 transfer
    worker2_stats.record_transfer(stats)

    # Worker 3: 3 transfers
    stats = get_default_xfer_telemetry(
        xferDurationS=2, postDurationS=2, totalBytes=2, descCount=2
    )
    worker3_stats.record_transfer(stats)
    worker3_stats.record_transfer(stats)
    worker3_stats.record_transfer(stats)

    # Create ModelRunnerOutput instances for each worker
    worker_outputs = []
    for i, worker_stats in enumerate([worker1_stats, worker2_stats, worker3_stats]):
        output = ModelRunnerOutput(
            req_ids=[f"req_{i}"],
            req_id_to_index={f"req_{i}": 0},
            sampled_token_ids=[[123]],  # dummy token
            logprobs=None,
            prompt_logprobs_dict={},
            pooler_output=[None],
            kv_connector_output=KVConnectorOutput(
                finished_sending=set([f"req_{i}_send"])
                if i < 2
                else None,  # Workers 0,1 finished sending
                finished_recving=set([f"req_{i}_recv"])
                if i > 0
                else None,  # Workers 1,2 finished receiving
                kv_connector_stats=worker_stats,
            ),
        )
        worker_outputs.append(output)

    # Use the real aggregation mechanism (like MultiprocExecutor.execute_model)
    aggregated_output = aggregator.aggregate(worker_outputs, output_rank=0)
    kv_connector_stats = aggregated_output.kv_connector_output.kv_connector_stats
    assert isinstance(kv_connector_stats, NixlKVConnectorStats)
    # Number of total transfers across all workers.
    assert kv_connector_stats.num_successful_transfers == 6
    # Logging proc, call reduce() to get CLI-friendly stats.
    cli_stats = kv_connector_stats.reduce()
    assert cli_stats["Avg xfer time (ms)"] == 1500.0
    assert cli_stats["Avg post time (ms)"] == 1500.0
    assert cli_stats["Avg number of descriptors"] == 1.5