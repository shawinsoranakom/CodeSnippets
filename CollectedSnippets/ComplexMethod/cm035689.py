async def test_run_controller_with_context_window_exceeded_without_truncation(
    mock_agent_with_stats,
    mock_runtime,
    mock_memory,
    test_event_stream,
):
    """Tests that the controller would quit upon context window exceeded errors without enable_history_truncation ON."""
    mock_agent, conversation_stats, llm_registry = mock_agent_with_stats

    class StepState:
        def __init__(self):
            self.has_errored = False

        def step(self, state: State):
            # If the state has more than one message and we haven't errored yet,
            # throw the context window exceeded error
            if len(state.history) > 3 and not self.has_errored:
                error = ContextWindowExceededError(
                    message='prompt is too long: 233885 tokens > 200000 maximum',
                    model='',
                    llm_provider='',
                )
                self.has_errored = True
                raise error

            return MessageAction(content=f'STEP {len(state.history)}')

    step_state = StepState()
    mock_agent.step = step_state.step
    mock_agent.config = AgentConfig()
    mock_agent.config.enable_history_truncation = False

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
    mock_runtime.event_stream = test_event_stream
    config = OpenHandsConfig(max_iterations=3)
    mock_runtime.config = copy.deepcopy(config)
    try:
        # Mock the create_agent function to return our mock agent
        with patch('openhands.core.main.create_agent', return_value=mock_agent):
            state = await asyncio.wait_for(
                run_controller(
                    config=config,
                    initial_user_action=MessageAction(content='INITIAL'),
                    runtime=mock_runtime,
                    sid='test',
                    fake_user_response_fn=lambda _: 'repeat',
                    memory=mock_memory,
                ),
                timeout=10,
            )

    # A timeout error indicates the run_controller entrypoint is not making
    # progress
    except asyncio.TimeoutError as e:
        raise AssertionError(
            'The run_controller function did not complete in time.'
        ) from e

    # Hitting the iteration limit indicates the controller is failing for the
    # expected reason
    # With the refactored system message handling, the iteration count is different
    assert state.iteration_flag.current_value == 1
    assert state.agent_state == AgentState.ERROR
    assert (
        state.last_error
        == 'LLMContextWindowExceedError: Conversation history longer than LLM context window limit. Consider turning on enable_history_truncation config to avoid this error'
    )

    error_observations = test_event_stream.get_matching_events(
        reverse=True, limit=1, event_types=(AgentStateChangedObservation)
    )
    assert len(error_observations) == 1
    error_observation = error_observations[0]
    assert (
        error_observation.reason
        == 'LLMContextWindowExceedError: Conversation history longer than LLM context window limit. Consider turning on enable_history_truncation config to avoid this error'
    )

    # Check that the context window exceeded error was raised during the run
    assert step_state.has_errored