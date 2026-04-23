def test_multi_kv_connector_stats_aggregation():
    """
    Test MultiKVConnectorStats aggregation across TP ranks using
    KVOutputAggregator (used by MultiprocExecutor).
    """

    aggregator = KVOutputAggregator(expected_finished_count=3)

    from dataclasses import dataclass

    # Mock a KVConnectorStats class for testing aggregation over connectors.
    @dataclass
    class FooKVConnectorStats(KVConnectorStats):
        def reset(self):
            self.data = {"num_foo_transfers": 0}

        def record_transfer(self):
            if "num_foo_transfers" not in self.data:
                self.data["num_foo_transfers"] = 0
            self.data["num_foo_transfers"] += 1

        def is_empty(self) -> bool:
            return self.data["num_foo_transfers"] == 0

        def aggregate(self, other: "FooKVConnectorStats") -> "FooKVConnectorStats":
            if not other.is_empty():
                self.data["num_foo_transfers"] += other.data["num_foo_transfers"]
            return self

    def make_multi_stats(nixl_count: int, foo_count: int) -> MultiKVConnectorStats:
        data: dict[str, KVConnectorStats] = {}
        if nixl_count > 0:
            nixl_stats = NixlKVConnectorStats()
            for _ in range(nixl_count):
                nixl_stats.record_transfer(get_default_xfer_telemetry())
            data["NixlConnector"] = nixl_stats
        if foo_count > 0:
            foo_stats = FooKVConnectorStats()
            for _ in range(foo_count):
                foo_stats.record_transfer()
            data["FooConnector"] = foo_stats
        return MultiKVConnectorStats(data=data)

    # Create heterogeneous stats across 3 workers
    worker_patterns = [(2, 1), (3, 0), (0, 5)]  # (Nixl, Foo)

    worker_outputs: list[ModelRunnerOutput] = []
    for i, (nixl_count, foo) in enumerate(worker_patterns):
        stats = make_multi_stats(nixl_count, foo)
        output = ModelRunnerOutput(
            req_ids=[f"req_{i}"],
            req_id_to_index={f"req_{i}": 0},
            sampled_token_ids=[[123]],
            logprobs=None,
            prompt_logprobs_dict={},
            pooler_output=[None],
            kv_connector_output=KVConnectorOutput(
                finished_sending=set([f"req_{i}_send"]) if i < 2 else None,
                finished_recving=set([f"req_{i}_recv"]) if i > 0 else None,
                kv_connector_stats=stats,
            ),
        )
        worker_outputs.append(output)

    aggregated_output = aggregator.aggregate(worker_outputs, output_rank=0)
    kv_connector_stats = aggregated_output.kv_connector_output.kv_connector_stats
    assert isinstance(kv_connector_stats, MultiKVConnectorStats)

    # Validate per-connector totals across workers
    assert isinstance(kv_connector_stats["NixlConnector"], NixlKVConnectorStats)
    assert kv_connector_stats["NixlConnector"].num_successful_transfers == 5
    assert isinstance(kv_connector_stats["FooConnector"], FooKVConnectorStats)
    assert kv_connector_stats["FooConnector"].data["num_foo_transfers"] == 6