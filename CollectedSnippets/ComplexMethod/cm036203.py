def test_histogram_metric(test_registry, num_engines):
    h = prometheus_client.Histogram(
        "vllm:test_histogram",
        "Test histogram metric",
        labelnames=["model", "engine_index"],
        buckets=[10, 20, 30, 40, 50],
        registry=test_registry,
    )
    for i in range(num_engines):
        hist = h.labels(model="blaa", engine_index=str(i))
        hist.observe(42)
        hist.observe(21)
        hist.observe(7)

    metrics = get_metrics_snapshot()
    assert len(metrics) == num_engines
    engine_labels = [str(i) for i in range(num_engines)]
    for m in metrics:
        assert isinstance(m, Histogram)
        assert m.name == "vllm:test_histogram"
        assert m.count == 3
        assert m.sum == 70
        assert m.buckets["10.0"] == 1
        assert m.buckets["20.0"] == 1
        assert m.buckets["30.0"] == 2
        assert m.buckets["40.0"] == 2
        assert m.buckets["50.0"] == 3
        assert m.labels["model"] == "blaa"
        assert m.labels["engine_index"] in engine_labels
        engine_labels.remove(m.labels["engine_index"])