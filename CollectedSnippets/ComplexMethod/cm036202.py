def test_counter_metric(test_registry, num_engines):
    c = prometheus_client.Counter(
        "vllm:test_counter",
        "Test counter metric",
        labelnames=["model", "engine_index"],
        registry=test_registry,
    )
    for i in range(num_engines):
        c.labels(model="bar", engine_index=str(i)).inc(19)

    metrics = get_metrics_snapshot()
    assert len(metrics) == num_engines
    engine_labels = [str(i) for i in range(num_engines)]
    for m in metrics:
        assert isinstance(m, Counter)
        assert m.name == "vllm:test_counter"
        assert m.value == 19
        assert m.labels["model"] == "bar"
        assert m.labels["engine_index"] in engine_labels
        engine_labels.remove(m.labels["engine_index"])