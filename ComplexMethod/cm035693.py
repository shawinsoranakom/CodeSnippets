async def test_agent_controller_processes_null_observation_with_cause(
    mock_agent_with_stats,
):
    """Test that AgentController processes NullObservation events with a cause value.

    And that the agent's step method is called as a result.
    """
    mock_agent, conversation_stats, llm_registry = mock_agent_with_stats

    # Create an in-memory file store and real event stream
    file_store = InMemoryFileStore()
    event_stream = EventStream(sid='test-session', file_store=file_store)

    # Create a Memory instance - not used directly in this test but needed for setup
    Memory(event_stream=event_stream, sid='test-session')

    # Create a controller with the mock agent
    controller = AgentController(
        agent=mock_agent,
        event_stream=event_stream,
        conversation_stats=conversation_stats,
        iteration_delta=10,
        sid='test-session',
    )

    # Patch the controller's step method to track calls
    with patch.object(controller, '_step') as mock_step:
        # Create and add the first user message (will have ID 0)
        user_message = MessageAction(content='First user message')
        user_message._source = EventSource.USER  # type: ignore[attr-defined]
        event_stream.add_event(user_message, EventSource.USER)

        # Give it a little time to process
        await asyncio.sleep(1)

        # Get all events from the stream
        events = list(event_stream.get_events())

        # Events in the stream:
        # Event 0: MessageAction, ID: 0, Cause: None, Source: EventSource.USER, Content: First user message
        # Event 1: RecallAction, ID: 1, Cause: None, Source: EventSource.USER, Content: N/A
        # Event 2: NullObservation, ID: 2, Cause: 1, Source: EventSource.ENVIRONMENT, Content:
        # Event 3: AgentStateChangedObservation, ID: 3, Cause: None, Source: EventSource.ENVIRONMENT, Content:

        # Find the RecallAction event (should be automatically created)
        recall_actions = [event for event in events if isinstance(event, RecallAction)]
        assert len(recall_actions) > 0, 'No RecallAction was created'
        recall_action = recall_actions[0]

        # Find any NullObservation events
        null_obs_events = [
            event for event in events if isinstance(event, NullObservation)
        ]
        assert len(null_obs_events) > 0, 'No NullObservation was created'
        null_observation = null_obs_events[0]

        # Verify the NullObservation has a cause that points to the RecallAction
        assert null_observation.cause is not None, 'NullObservation cause is None'
        assert null_observation.cause == recall_action.id, (
            f'Expected cause={recall_action.id}, got cause={null_observation.cause}'
        )

        # Verify the controller's should_step method returns True for this observation
        assert controller.should_step(null_observation), (
            'should_step should return True for this NullObservation'
        )

        # Verify the controller's step method was called
        # This means the controller processed the NullObservation
        assert mock_step.called, "Controller's step method was not called"

        # Now test with a NullObservation that has cause=0
        # Create a NullObservation with cause = 0 (pointing to the first user message)
        null_observation_zero = NullObservation(content='Test observation with cause=0')
        null_observation_zero._cause = 0  # type: ignore[attr-defined]

        # Verify the controller's should_step method would return False for this observation
        assert not controller.should_step(null_observation_zero), (
            'should_step should return False for NullObservation with cause=0'
        )