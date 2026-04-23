async def test_run_controller_stop_with_stuck(
    test_event_stream, mock_memory, mock_agent_with_stats
):
    config = OpenHandsConfig()
    mock_agent, conversation_stats, llm_registry = mock_agent_with_stats

    def agent_step_fn(state):
        print(f'agent_step_fn received state: {state}')
        return CmdRunAction(command='ls')

    mock_agent.step = agent_step_fn

    runtime = MagicMock(spec=ActionExecutionClient)

    def on_event(event: Event):
        if isinstance(event, CmdRunAction):
            non_fatal_error_obs = ErrorObservation(
                'Non fatal error here to trigger loop'
            )
            non_fatal_error_obs._cause = event.id
            test_event_stream.add_event(non_fatal_error_obs, EventSource.ENVIRONMENT)

    test_event_stream.subscribe(EventStreamSubscriber.RUNTIME, on_event, str(uuid4()))
    runtime.event_stream = test_event_stream
    runtime.config = copy.deepcopy(config)

    def on_event_memory(event: Event):
        if isinstance(event, RecallAction):
            microagent_obs = RecallObservation(
                content='Test microagent content',
                recall_type=RecallType.KNOWLEDGE,
            )
            microagent_obs._cause = event.id
            test_event_stream.add_event(microagent_obs, EventSource.ENVIRONMENT)

    test_event_stream.subscribe(
        EventStreamSubscriber.MEMORY, on_event_memory, str(uuid4())
    )

    # Mock the create_agent function to return our mock agent
    with patch('openhands.core.main.create_agent', return_value=mock_agent):
        state = await run_controller(
            config=config,
            initial_user_action=MessageAction(content='Test message'),
            runtime=runtime,
            sid='test',
            fake_user_response_fn=lambda _: 'repeat',
            memory=mock_memory,
        )
    events = list(test_event_stream.get_events())
    print(f'state: {state}')
    for i, event in enumerate(events):
        print(f'event {i}: {event_to_dict(event)}')

    assert state.iteration_flag.current_value == 3
    assert len(events) == 12
    # check the eventstream have 4 pairs of repeated actions and observations
    # With the refactored system message handling, we need to adjust the range
    repeating_actions_and_observations = events[5:13]
    for action, observation in zip(
        repeating_actions_and_observations[0::2],
        repeating_actions_and_observations[1::2],
    ):
        action_dict = event_to_dict(action)
        observation_dict = event_to_dict(observation)
        assert action_dict['action'] == 'run' and action_dict['args']['command'] == 'ls'
        assert (
            observation_dict['observation'] == 'error'
            and observation_dict['content'] == 'Non fatal error here to trigger loop'
        )
    last_event = event_to_dict(events[-1])
    assert last_event['extras']['agent_state'] == 'error'
    assert last_event['observation'] == 'agent_state_changed'

    assert state.agent_state == AgentState.ERROR
    assert state.last_error == 'AgentStuckInLoopError: Agent got stuck in a loop'