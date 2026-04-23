def test_metrics_basic_serialization():
    # Create a basic action with only accumulated_cost
    action = MessageAction(content='Hello, world!')
    metrics = Metrics()
    metrics.accumulated_cost = 0.03
    action._llm_metrics = metrics

    # Test serialization
    serialized = event_to_dict(action)
    assert 'llm_metrics' in serialized
    assert serialized['llm_metrics']['accumulated_cost'] == 0.03
    assert serialized['llm_metrics']['costs'] == []
    assert serialized['llm_metrics']['response_latencies'] == []
    assert serialized['llm_metrics']['token_usages'] == []

    # Test deserialization
    deserialized = event_from_dict(serialized)
    assert deserialized.llm_metrics is not None
    assert deserialized.llm_metrics.accumulated_cost == 0.03
    assert len(deserialized.llm_metrics.costs) == 0
    assert len(deserialized.llm_metrics.response_latencies) == 0
    assert len(deserialized.llm_metrics.token_usages) == 0