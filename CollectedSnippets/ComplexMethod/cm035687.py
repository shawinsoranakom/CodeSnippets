async def test_budget_reset_on_continue(mock_agent_with_stats, mock_event_stream):
    """Test that when a user continues after hitting the budget limit:
    1. Error is thrown when budget cap is exceeded
    2. LLM budget does not reset when user continues
    3. Budget is extended by adding the initial budget cap to the current accumulated cost
    """
    mock_agent, conversation_stats, llm_registry = mock_agent_with_stats

    # Create a real Metrics instance shared between controller state and llm
    metrics = Metrics()
    metrics.accumulated_cost = 6.0

    initial_budget = 5.0

    initial_state = State(
        metrics=metrics,
        budget_flag=BudgetControlFlag(
            limit_increase_amount=initial_budget,
            current_value=6.0,
            max_value=initial_budget,
        ),
    )

    # Update agent's LLM metrics in place
    mock_agent.llm.metrics.accumulated_cost = metrics.accumulated_cost

    # Create controller with budget cap
    controller = AgentController(
        agent=mock_agent,
        event_stream=mock_event_stream,
        conversation_stats=conversation_stats,
        iteration_delta=10,
        budget_per_task_delta=initial_budget,
        sid='test',
        confirmation_mode=False,
        headless_mode=False,
        initial_state=initial_state,
    )

    # Set up initial state
    controller.state.agent_state = AgentState.RUNNING

    # Set up metrics to simulate having spent more than the budget
    assert controller.state.budget_flag.current_value == 6.0
    assert controller.agent.llm.metrics.accumulated_cost == 6.0

    # Trigger budget limit
    await controller._step()

    # Verify budget limit was hit and error was thrown
    assert controller.state.agent_state == AgentState.ERROR
    assert 'budget' in controller.state.last_error.lower()

    # Now set the agent state to RUNNING (simulating user clicking "continue")
    await controller.set_agent_state_to(AgentState.RUNNING)

    # Now simulate user sending a message
    message_action = MessageAction(content='Please continue')
    message_action._source = EventSource.USER
    await controller._on_event(message_action)

    # Verify budget cap was extended by adding initial budget to current accumulated cost
    # accumulated cost (6.0) + initial budget (5.0) = 11.0
    assert controller.state.budget_flag.max_value == 11.0

    # Verify LLM metrics were NOT reset - they should still be 6.0
    assert controller.agent.llm.metrics.accumulated_cost == 6.0

    # The controller state metrics are same as llm metrics
    assert controller.state.metrics.accumulated_cost == 6.0

    # Verify traffic control state was reset
    await controller.close()