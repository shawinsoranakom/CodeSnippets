def test_multiple_llm_services(connected_registry_and_stats):
    """Test tracking metrics for multiple LLM services."""
    mock_llm_registry, conversation_stats = connected_registry_and_stats

    # Create multiple LLMs through the registry
    service1 = 'service1'
    service2 = 'service2'

    llm_config1 = LLMConfig(
        model='gpt-4o',
        api_key='test_key',
        num_retries=2,
        retry_min_wait=1,
        retry_max_wait=2,
    )

    llm_config2 = LLMConfig(
        model='gpt-3.5-turbo',
        api_key='test_key',
        num_retries=2,
        retry_min_wait=1,
        retry_max_wait=2,
    )

    # Get LLMs from registry (this should trigger notifications)
    llm1 = mock_llm_registry.get_llm(service1, llm_config1)
    llm2 = mock_llm_registry.get_llm(service2, llm_config2)

    # Add different metrics to each LLM
    llm1.metrics.add_cost(0.05)
    llm1.metrics.add_token_usage(
        prompt_tokens=100,
        completion_tokens=50,
        cache_read_tokens=0,
        cache_write_tokens=0,
        context_window=8000,
        response_id='resp1',
    )

    llm2.metrics.add_cost(0.02)
    llm2.metrics.add_token_usage(
        prompt_tokens=200,
        completion_tokens=100,
        cache_read_tokens=0,
        cache_write_tokens=0,
        context_window=4000,
        response_id='resp2',
    )

    # Verify services were registered in conversation stats
    assert service1 in conversation_stats.service_to_metrics
    assert service2 in conversation_stats.service_to_metrics

    # Verify individual metrics
    assert conversation_stats.service_to_metrics[service1].accumulated_cost == 0.05
    assert conversation_stats.service_to_metrics[service2].accumulated_cost == 0.02

    # Get combined metrics and verify
    combined = conversation_stats.get_combined_metrics()
    assert combined.accumulated_cost == 0.07  # 0.05 + 0.02
    assert combined.accumulated_token_usage.prompt_tokens == 300  # 100 + 200
    assert combined.accumulated_token_usage.completion_tokens == 150  # 50 + 100
    assert (
        combined.accumulated_token_usage.context_window == 8000
    )