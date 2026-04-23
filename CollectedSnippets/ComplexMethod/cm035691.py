async def test_condenser_metrics_included(mock_agent_with_stats, test_event_stream):
    """Test that metrics from the condenser's LLM are included in the action metrics."""
    mock_agent, conversation_stats, llm_registry = mock_agent_with_stats

    # Set up agent metrics in place
    mock_agent.llm.metrics.accumulated_cost = 0.05
    mock_agent.llm.metrics._accumulated_token_usage = TokenUsage(
        model='agent-model',
        prompt_tokens=100,
        completion_tokens=50,
        cache_read_tokens=10,
        cache_write_tokens=10,
        response_id='agent-accumulated',
    )
    mock_agent.name = 'TestAgent'

    # Create condenser with its own metrics
    condenser = MagicMock()
    condenser.llm = MagicMock(spec=LLM)
    condenser_metrics = Metrics(model_name='condenser-model')
    condenser_metrics.accumulated_cost = 0.03
    condenser_metrics._accumulated_token_usage = TokenUsage(
        model='condenser-model',
        prompt_tokens=200,
        completion_tokens=100,
        cache_read_tokens=20,
        cache_write_tokens=5000,  # High cache_write value that should be preserved
        response_id='condenser-accumulated',
    )
    condenser.llm.metrics = condenser_metrics

    # Register the condenser metrics with the LLM registry
    llm_registry.service_to_llm['condenser'] = condenser.llm
    # Manually notify the conversation stats about the condenser LLM registration
    llm_registry.notify(RegistryEvent(llm=condenser.llm, service_id='condenser'))

    # Attach the condenser to the mock_agent
    mock_agent.condenser = condenser

    def agent_step_fn(state):
        # Create a new CondensationAction each time to avoid ID reuse
        action = CondensationAction(
            forgotten_events_start_id=1,
            forgotten_events_end_id=5,
            summary='Test summary',
            summary_offset=1,
        )
        action._source = EventSource.AGENT  # Required for event_stream.add_event
        return action

    mock_agent.step = agent_step_fn

    # Create controller with correct parameters
    controller = AgentController(
        agent=mock_agent,
        event_stream=test_event_stream,
        conversation_stats=conversation_stats,
        iteration_delta=10,
        sid='test',
        confirmation_mode=False,
        headless_mode=True,
        initial_state=State(metrics=mock_agent.llm.metrics, budget_flag=None),
    )

    # Execute one step
    controller.state.agent_state = AgentState.RUNNING
    await controller._step()

    # Get the last event from event stream
    events = list(test_event_stream.get_events())
    assert len(events) > 0
    last_action = events[-1]

    # Verify metrics were copied correctly
    assert last_action.llm_metrics is not None

    # Verify that both agent and condenser metrics are included
    assert last_action.llm_metrics.accumulated_cost == pytest.approx(
        0.08
    )  # 0.05 from agent + 0.03 from condenser

    # The accumulated token usage should include both agent and condenser metrics
    assert (
        last_action.llm_metrics.accumulated_token_usage.prompt_tokens == 300
    )  # 100 + 200
    assert (
        last_action.llm_metrics.accumulated_token_usage.completion_tokens == 150
    )  # 50 + 100
    assert (
        last_action.llm_metrics.accumulated_token_usage.cache_read_tokens == 30
    )  # 10 + 20
    assert (
        last_action.llm_metrics.accumulated_token_usage.cache_write_tokens == 5010
    )  # 10 + 5000

    await controller.close()