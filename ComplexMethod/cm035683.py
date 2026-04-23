async def test_delegation_flow(
    mock_parent_agent, mock_child_agent, mock_event_stream, connected_registry_and_stats
):
    """
    Test that when the parent agent delegates to a child
     1. the parent's delegate is set, and once the child finishes, the parent is cleaned up properly.
     2. metrics are accumulated globally via LLM registry (delegate adds to the global metrics)
     3. global metrics tracking works correctly through the LLM registry
    """
    llm_registry, conversation_stats = connected_registry_and_stats

    # Mock the agent class resolution so that AgentController can instantiate mock_child_agent
    Agent.get_cls = Mock(
        return_value=create_mock_agent_factory(mock_child_agent, llm_registry)
    )

    step_count = 0

    def agent_step_fn(state):
        nonlocal step_count
        step_count += 1
        return CmdRunAction(command=f'ls {step_count}')

    mock_child_agent.step = agent_step_fn

    # Set up the parent agent's LLM with initial cost and register it in the registry
    # The parent agent's LLM should use the existing registered LLM to ensure proper tracking
    parent_llm = llm_registry.service_to_llm['agent']
    parent_llm.metrics.accumulated_cost = 2
    mock_parent_agent.llm = parent_llm

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
            current_value=1, limit_increase_amount=10, max_value=10
        ),
    )

    parent_controller = AgentController(
        agent=mock_parent_agent,
        event_stream=mock_event_stream,
        conversation_stats=conversation_stats,
        iteration_delta=1,  # Add the required iteration_delta parameter
        sid='parent',
        confirmation_mode=False,
        headless_mode=True,
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

    # The parent's iteration should have incremented
    assert parent_controller.state.iteration_flag.current_value == 2, (
        'Parent iteration should be incremented after step.'
    )

    # Now simulate that the child increments local iteration and finishes its subtask
    delegate_controller = parent_controller.delegate

    # Take four delegate steps; mock cost per step
    for i in range(4):
        delegate_controller.state.iteration_flag.step()
        delegate_controller.agent.step(delegate_controller.state)
        # Update the agent's LLM metrics (not the deprecated state metrics)
        delegate_controller.agent.llm.metrics.add_cost(1.0)

    assert (
        delegate_controller.state.get_local_step() == 4
    )  # verify local metrics are accessible via snapshot

    # Check that the conversation stats has the combined metrics (parent + delegate)
    combined_metrics = (
        delegate_controller.state.conversation_stats.get_combined_metrics()
    )
    assert (
        combined_metrics.accumulated_cost
        == 6  # Make sure delegate tracks global cost (2 from parent + 4 from delegate)
    )

    # Since metrics are now global via LLM registry, local metrics tracking
    # is handled differently. The delegate's LLM shares the same metrics object
    # as the parent for global tracking, so we verify the global total is correct.

    delegate_controller.state.outputs = {'delegate_result': 'done'}

    # The child is done, so we simulate it finishing:
    child_finish_action = AgentFinishAction()
    await delegate_controller._on_event(child_finish_action)
    await asyncio.sleep(0.5)

    # Now the parent's delegate is None
    assert parent_controller.delegate is None, (
        'Parent delegate should be None after child finishes.'
    )

    # Parent's global iteration is updated from the child
    assert parent_controller.state.iteration_flag.current_value == 7, (
        "Parent iteration should be the child's iteration + 1 after child is done."
    )

    # Cleanup
    await parent_controller.close()