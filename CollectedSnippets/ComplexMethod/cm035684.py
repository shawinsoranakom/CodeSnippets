async def test_delegate_hits_global_limits(
    mock_child_agent, mock_event_stream, mock_parent_agent, connected_registry_and_stats
):
    """
    Global limits from control flags should apply to delegates
    """
    llm_registry, conversation_stats = connected_registry_and_stats

    # Mock the agent class resolution so that AgentController can instantiate mock_child_agent
    Agent.get_cls = Mock(
        return_value=create_mock_agent_factory(mock_child_agent, llm_registry)
    )

    # Set up the parent agent's LLM with initial cost and register it in the registry
    mock_parent_agent.llm.metrics.accumulated_cost = 2
    mock_parent_agent.llm.service_id = 'main_agent'
    # Register the parent agent's LLM in the registry
    llm_registry.service_to_llm['main_agent'] = mock_parent_agent.llm

    parent_metrics = Metrics()
    parent_metrics.accumulated_cost = 2
    # Create parent controller
    parent_state = State(
        inputs={},
        metrics=parent_metrics,
        budget_flag=BudgetControlFlag(
            current_value=2, limit_increase_amount=10, max_value=10
        ),
        iteration_flag=IterationControlFlag(
            current_value=2, limit_increase_amount=3, max_value=3
        ),
    )

    parent_controller = AgentController(
        agent=mock_parent_agent,
        event_stream=mock_event_stream,
        conversation_stats=conversation_stats,
        iteration_delta=1,  # Add the required iteration_delta parameter
        sid='parent',
        confirmation_mode=False,
        headless_mode=False,
        initial_state=parent_state,
    )

    # Setup Memory to catch RecallActions
    mock_memory = MagicMock(spec=Memory)
    mock_memory.event_stream = mock_event_stream

    def on_event(event: Event):
        if isinstance(event, RecallAction):
            # create a RecallObservation
            microagent_observation = RecallObservation(
                recall_type=RecallType.KNOWLEDGE,
                content='Found info',
            )
            microagent_observation._cause = event.id  # ignore attr-defined warning
            mock_event_stream.add_event(microagent_observation, EventSource.ENVIRONMENT)

    mock_memory.on_event = on_event
    mock_event_stream.subscribe(
        EventStreamSubscriber.MEMORY, mock_memory.on_event, mock_memory
    )

    # Setup a delegate action from the parent
    delegate_action = AgentDelegateAction(agent='ChildAgent', inputs={'test': True})
    mock_parent_agent.step.return_value = delegate_action

    # Simulate a user message event to cause parent.step() to run
    message_action = MessageAction(content='please delegate now')
    message_action._source = EventSource.USER
    await parent_controller._on_event(message_action)

    # Give time for the async step() to execute
    await asyncio.sleep(1)

    # Verify that a RecallObservation was added to the event stream
    events = list(mock_event_stream.get_events())

    # The exact number of events might vary depending on implementation details
    # Just verify that we have at least a few events
    assert mock_event_stream.get_latest_event_id() >= 3

    # a RecallObservation and an AgentDelegateAction should be in the list
    assert any(isinstance(event, RecallObservation) for event in events)
    assert any(isinstance(event, AgentDelegateAction) for event in events)

    # Verify that a delegate agent controller is created
    assert parent_controller.delegate is not None, (
        "Parent's delegate controller was not set."
    )

    delegate_controller = parent_controller.delegate
    await delegate_controller.set_agent_state_to(AgentState.RUNNING)

    # Step should hit max budget
    message_action = MessageAction(content='Test message')
    message_action._source = EventSource.USER

    await delegate_controller._on_event(message_action)
    await asyncio.sleep(0.1)

    assert delegate_controller.state.agent_state == AgentState.ERROR
    assert (
        delegate_controller.state.last_error
        == 'RuntimeError: Agent reached maximum iteration. Current iteration: 3, max iteration: 3'
    )

    await delegate_controller.set_agent_state_to(AgentState.RUNNING)
    await asyncio.sleep(0.1)

    assert delegate_controller.state.iteration_flag.max_value == 6
    assert (
        delegate_controller.state.iteration_flag.max_value
        == parent_controller.state.iteration_flag.max_value
    )

    message_action = MessageAction(content='Test message 2')
    message_action._source = EventSource.USER
    await delegate_controller._on_event(message_action)
    await asyncio.sleep(0.1)

    assert delegate_controller.state.iteration_flag.current_value == 4
    assert (
        delegate_controller.state.iteration_flag.current_value
        == parent_controller.state.iteration_flag.current_value
    )