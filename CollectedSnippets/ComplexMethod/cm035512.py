def test_llm_registry_notifications(connected_registry_and_stats):
    """Test that LLM registry notifications update conversation stats."""
    mock_llm_registry, conversation_stats = connected_registry_and_stats

    # Create a new LLM through the registry
    service_id = 'test-service'
    llm_config = LLMConfig(
        model='gpt-4o',
        api_key='test_key',
        num_retries=2,
        retry_min_wait=1,
        retry_max_wait=2,
    )

    # Get LLM from registry (this should trigger the notification)
    llm = mock_llm_registry.get_llm(service_id, llm_config)

    # Verify the service was registered in conversation stats
    assert service_id in conversation_stats.service_to_metrics
    assert conversation_stats.service_to_metrics[service_id] is llm.metrics

    # Add some metrics to the LLM
    llm.metrics.add_cost(0.05)
    llm.metrics.add_token_usage(
        prompt_tokens=100,
        completion_tokens=50,
        cache_read_tokens=0,
        cache_write_tokens=0,
        context_window=8000,
        response_id='resp1',
    )

    # Verify the metrics are reflected in conversation stats
    assert conversation_stats.service_to_metrics[service_id].accumulated_cost == 0.05
    assert (
        conversation_stats.service_to_metrics[
            service_id
        ].accumulated_token_usage.prompt_tokens
        == 100
    )
    assert (
        conversation_stats.service_to_metrics[
            service_id
        ].accumulated_token_usage.completion_tokens
        == 50
    )

    # Get combined metrics and verify
    combined = conversation_stats.get_combined_metrics()
    assert combined.accumulated_cost == 0.05
    assert combined.accumulated_token_usage.prompt_tokens == 100
    assert combined.accumulated_token_usage.completion_tokens == 50