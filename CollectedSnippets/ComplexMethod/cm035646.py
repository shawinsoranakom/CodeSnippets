def test_metrics_full_serialization():
    # Create an observation with all metrics fields
    obs = CmdOutputObservation(
        command='ls',
        content='test.txt',
        metadata=CmdOutputMetadata(exit_code=0),
    )
    metrics = Metrics(model_name='test-model')
    metrics.accumulated_cost = 0.03

    # Add a cost
    cost = Cost(model='test-model', cost=0.02)
    metrics._costs.append(cost)

    # Add a response latency
    latency = ResponseLatency(model='test-model', latency=0.5, response_id='test-id')
    metrics.response_latencies = [latency]

    # Add token usage
    usage = TokenUsage(
        model='test-model',
        prompt_tokens=10,
        completion_tokens=20,
        cache_read_tokens=0,
        cache_write_tokens=0,
        response_id='test-id',
    )
    metrics.token_usages = [usage]

    obs._llm_metrics = metrics

    # Test serialization
    serialized = event_to_dict(obs)
    assert 'llm_metrics' in serialized
    metrics_dict = serialized['llm_metrics']
    assert metrics_dict['accumulated_cost'] == 0.03
    assert len(metrics_dict['costs']) == 1
    assert metrics_dict['costs'][0]['cost'] == 0.02
    assert len(metrics_dict['response_latencies']) == 1
    assert metrics_dict['response_latencies'][0]['latency'] == 0.5
    assert len(metrics_dict['token_usages']) == 1
    assert metrics_dict['token_usages'][0]['prompt_tokens'] == 10
    assert metrics_dict['token_usages'][0]['completion_tokens'] == 20

    # Test deserialization
    deserialized = event_from_dict(serialized)
    assert deserialized.llm_metrics is not None
    assert deserialized.llm_metrics.accumulated_cost == 0.03
    assert len(deserialized.llm_metrics.costs) == 1
    assert deserialized.llm_metrics.costs[0].cost == 0.02
    assert len(deserialized.llm_metrics.response_latencies) == 1
    assert deserialized.llm_metrics.response_latencies[0].latency == 0.5
    assert len(deserialized.llm_metrics.token_usages) == 1
    assert deserialized.llm_metrics.token_usages[0].prompt_tokens == 10
    assert deserialized.llm_metrics.token_usages[0].completion_tokens == 20