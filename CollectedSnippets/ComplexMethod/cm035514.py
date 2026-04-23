def test_save_and_restore_workflow(mock_file_store):
    """Test the full workflow of saving and restoring metrics."""
    # Create initial conversation stats
    conversation_id = 'test-conversation-id'
    user_id = 'test-user-id'

    stats1 = ConversationStats(
        file_store=mock_file_store, conversation_id=conversation_id, user_id=user_id
    )

    # Add a service with metrics
    service_id = 'test-service'
    metrics = Metrics(model_name='gpt-4')
    metrics.add_cost(0.05)
    metrics.add_token_usage(
        prompt_tokens=100,
        completion_tokens=50,
        cache_read_tokens=0,
        cache_write_tokens=0,
        context_window=8000,
        response_id='resp1',
    )
    stats1.service_to_metrics[service_id] = metrics

    # Save metrics
    stats1.save_metrics()

    # Create a new conversation stats instance that should restore the metrics
    stats2 = ConversationStats(
        file_store=mock_file_store, conversation_id=conversation_id, user_id=user_id
    )

    # Verify metrics were restored
    assert service_id in stats2.restored_metrics
    assert stats2.restored_metrics[service_id].accumulated_cost == 0.05
    assert (
        stats2.restored_metrics[service_id].accumulated_token_usage.prompt_tokens == 100
    )
    assert (
        stats2.restored_metrics[service_id].accumulated_token_usage.completion_tokens
        == 50
    )

    # Create a real LLM instance with a mock config
    llm_config = LLMConfig(
        model='gpt-4o',
        api_key='test_key',
        num_retries=2,
        retry_min_wait=1,
        retry_max_wait=2,
    )

    # Patch the LLM class to avoid actual API calls
    with patch('openhands.llm.llm.litellm_completion'):
        llm = LLM(service_id=service_id, config=llm_config)

        # Create a registry event
        event = RegistryEvent(llm=llm, service_id=service_id)

        # Register the LLM to trigger restoration
        stats2.register_llm(event)

        # Verify metrics were applied to the LLM
        assert llm.metrics.accumulated_cost == 0.05
        assert llm.metrics.accumulated_token_usage.prompt_tokens == 100
        assert llm.metrics.accumulated_token_usage.completion_tokens == 50