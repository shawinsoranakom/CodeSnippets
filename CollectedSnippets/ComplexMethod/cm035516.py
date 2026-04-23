def test_save_metrics_preserves_restored_metrics_fix(mock_file_store):
    """Test that save_metrics correctly preserves restored metrics for unregistered services."""
    conversation_id = 'test-conversation-id'
    user_id = 'test-user-id'

    # Step 1: Create initial conversation stats with multiple services
    stats1 = ConversationStats(
        file_store=mock_file_store, conversation_id=conversation_id, user_id=user_id
    )

    # Add metrics for multiple services
    service_a = 'service-a'
    service_b = 'service-b'
    service_c = 'service-c'

    metrics_a = Metrics(model_name='gpt-4')
    metrics_a.add_cost(0.10)

    metrics_b = Metrics(model_name='gpt-3.5')
    metrics_b.add_cost(0.05)

    metrics_c = Metrics(model_name='claude-3')
    metrics_c.add_cost(0.08)

    stats1.service_to_metrics[service_a] = metrics_a
    stats1.service_to_metrics[service_b] = metrics_b
    stats1.service_to_metrics[service_c] = metrics_c

    # Save metrics (all three services should be saved)
    stats1.save_metrics()

    # Step 2: Create new conversation stats instance (simulates app restart)
    stats2 = ConversationStats(
        file_store=mock_file_store, conversation_id=conversation_id, user_id=user_id
    )

    # Verify all metrics were restored
    assert service_a in stats2.restored_metrics
    assert service_b in stats2.restored_metrics
    assert service_c in stats2.restored_metrics
    assert stats2.restored_metrics[service_a].accumulated_cost == 0.10
    assert stats2.restored_metrics[service_b].accumulated_cost == 0.05
    assert stats2.restored_metrics[service_c].accumulated_cost == 0.08

    # Step 3: Register only one LLM service (simulates partial LLM activation)
    llm_config = LLMConfig(
        model='gpt-4o',
        api_key='test_key',
        num_retries=2,
        retry_min_wait=1,
        retry_max_wait=2,
    )

    with patch('openhands.llm.llm.litellm_completion'):
        llm_a = LLM(service_id=service_a, config=llm_config)
        event_a = RegistryEvent(llm=llm_a, service_id=service_a)
        stats2.register_llm(event_a)

    # Verify service_a was moved from restored_metrics to service_to_metrics
    assert service_a in stats2.service_to_metrics
    assert service_a not in stats2.restored_metrics
    assert stats2.service_to_metrics[service_a].accumulated_cost == 0.10

    # Verify services B and C are still in restored_metrics (not yet registered)
    assert service_b in stats2.restored_metrics
    assert service_c in stats2.restored_metrics
    assert stats2.restored_metrics[service_b].accumulated_cost == 0.05
    assert stats2.restored_metrics[service_c].accumulated_cost == 0.08

    # Step 4: Save metrics again (this is where the bug occurs)
    stats2.save_metrics()

    # Step 5: Create a third conversation stats instance to verify what was saved
    stats3 = ConversationStats(
        file_store=mock_file_store, conversation_id=conversation_id, user_id=user_id
    )

    # FIXED: All services should be restored because save_metrics now combines both dictionaries
    # Service A should be restored with its current metrics from service_to_metrics
    assert service_a in stats3.restored_metrics
    assert stats3.restored_metrics[service_a].accumulated_cost == 0.10

    # Services B and C should be preserved from restored_metrics
    assert service_b in stats3.restored_metrics  # FIXED: Now preserved
    assert service_c in stats3.restored_metrics  # FIXED: Now preserved
    assert stats3.restored_metrics[service_b].accumulated_cost == 0.05
    assert stats3.restored_metrics[service_c].accumulated_cost == 0.08