def test_vector_metric(test_registry, num_engines):
    c = prometheus_client.Counter(
        "vllm:spec_decode_num_accepted_tokens_per_pos",
        "Vector-like counter metric",
        labelnames=["position", "model", "engine_index"],
        registry=test_registry,
    )
    for i in range(num_engines):
        c.labels(position="0", model="llama", engine_index=str(i)).inc(10)
        c.labels(position="1", model="llama", engine_index=str(i)).inc(5)
        c.labels(position="2", model="llama", engine_index=str(i)).inc(1)

    metrics = get_metrics_snapshot()
    assert len(metrics) == num_engines
    engine_labels = [str(i) for i in range(num_engines)]
    for m in metrics:
        assert isinstance(m, Vector)
        assert m.name == "vllm:spec_decode_num_accepted_tokens_per_pos"
        assert m.values == [10, 5, 1]
        assert m.labels["model"] == "llama"
        assert m.labels["engine_index"] in engine_labels
        engine_labels.remove(m.labels["engine_index"])