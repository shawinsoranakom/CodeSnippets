async def test_action_metrics_copy(mock_agent_with_stats):
    mock_agent, conversation_stats, llm_registry = mock_agent_with_stats

    # Setup
    file_store = InMemoryFileStore({})
    event_stream = EventStream(sid='test', file_store=file_store)

    metrics = Metrics(model_name='test-model')
    metrics.accumulated_cost = 0.05

    initial_state = State(metrics=metrics, budget_flag=None)

    # Update agent's LLM metrics

    # Add multiple token usages - we should get the last one in the action
    usage1 = TokenUsage(
        model='test-model',
        prompt_tokens=5,
        completion_tokens=10,
        cache_read_tokens=2,
        cache_write_tokens=2,
        response_id='test-id-1',
    )

    usage2 = TokenUsage(
        model='test-model',
        prompt_tokens=10,
        completion_tokens=20,
        cache_read_tokens=5,
        cache_write_tokens=5,
        response_id='test-id-2',
    )

    metrics.token_usages = [usage1, usage2]

    # Set the accumulated token usage
    metrics._accumulated_token_usage = TokenUsage(
        model='test-model',
        prompt_tokens=15,  # 5 + 10
        completion_tokens=30,  # 10 + 20
        cache_read_tokens=7,  # 2 + 5
        cache_write_tokens=7,  # 2 + 5
        response_id='accumulated',
    )

    # Add a cost instance - should not be included in action metrics
    # This will increase accumulated_cost by 0.02
    metrics.add_cost(0.02)

    # Add a response latency - should not be included in action metrics
    metrics.add_response_latency(0.5, 'test-id-2')

    mock_agent.llm.metrics = metrics

    # Register the metrics with the LLM registry
    llm_registry.service_to_llm['agent'] = mock_agent.llm
    # Manually notify the conversation stats about the LLM registration
    llm_registry.notify(RegistryEvent(llm=mock_agent.llm, service_id='agent'))

    # Mock agent step to return an action
    action = MessageAction(content='Test message')

    def agent_step_fn(state):
        return action

    mock_agent.step = agent_step_fn

    # Create controller with correct parameters
    controller = AgentController(
        agent=mock_agent,
        event_stream=event_stream,
        conversation_stats=conversation_stats,
        iteration_delta=10,
        sid='test',
        confirmation_mode=False,
        headless_mode=True,
        initial_state=initial_state,
    )

    # Execute one step
    controller.state.agent_state = AgentState.RUNNING
    await controller._step()

    # Get the last event from event stream
    events = list(event_stream.get_events())
    assert len(events) > 0
    last_action = events[-1]

    # Verify metrics were copied correctly
    assert last_action.llm_metrics is not None
    assert (
        last_action.llm_metrics.accumulated_cost == 0.07
    )  # 0.05 initial + 0.02 from add_cost

    # Should not include individual token usages anymore (after the fix)
    assert len(last_action.llm_metrics.token_usages) == 0

    # But should include the accumulated token usage
    assert last_action.llm_metrics.accumulated_token_usage.prompt_tokens == 15  # 5 + 10
    assert (
        last_action.llm_metrics.accumulated_token_usage.completion_tokens == 30
    )  # 10 + 20
    assert (
        last_action.llm_metrics.accumulated_token_usage.cache_read_tokens == 7
    )  # 2 + 5
    assert (
        last_action.llm_metrics.accumulated_token_usage.cache_write_tokens == 7
    )  # 2 + 5

    # Should not include the cost history
    assert len(last_action.llm_metrics.costs) == 0

    # Should not include the response latency history
    assert len(last_action.llm_metrics.response_latencies) == 0

    # Verify that there's no latency information in the action's metrics
    # Either directly or as a calculated property
    assert not hasattr(last_action.llm_metrics, 'latency')
    assert not hasattr(last_action.llm_metrics, 'total_latency')
    assert not hasattr(last_action.llm_metrics, 'average_latency')

    # Verify it's a deep copy by modifying the original
    mock_agent.llm.metrics.accumulated_cost = 0.1
    assert last_action.llm_metrics.accumulated_cost == 0.07

    await controller.close()