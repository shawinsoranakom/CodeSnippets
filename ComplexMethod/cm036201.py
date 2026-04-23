def test_gauge_metric(test_registry, num_engines):
    g = prometheus_client.Gauge(
        "vllm:test_gauge",
        "Test gauge metric",
        labelnames=["model", "engine_index"],
        registry=test_registry,
    )
    for i in range(num_engines):
        g.labels(model="foo", engine_index=str(i)).set(98.5)

    metrics = get_metrics_snapshot()
    assert len(metrics) == num_engines
    engine_labels = [str(i) for i in range(num_engines)]
    for m in metrics:
        assert isinstance(m, Gauge)
        assert m.name == "vllm:test_gauge"
        assert m.value == 98.5
        assert m.labels["model"] == "foo"
        assert m.labels["engine_index"] in engine_labels
        engine_labels.remove(m.labels["engine_index"])