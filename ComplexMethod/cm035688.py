async def test_context_window_exceeded_error_handling(
    context_window_error,
    mock_agent_with_stats,
    mock_runtime,
    test_event_stream,
    mock_memory,
):
    """Test that context window exceeded errors are handled correctly by the controller, providing a smaller view but keeping the history intact."""
    mock_agent, conversation_stats, llm_registry = mock_agent_with_stats

    max_iterations = 5
    error_after = 2

    class StepState:
        def __init__(self):
            self.has_errored = False
            self.index = 0
            self.views = []
            self.condenser = ConversationWindowCondenser()

        def step(self, state: State):
            match self.condenser.condense(state.view):
                case View() as view:
                    self.views.append(view)

                case Condensation(action=action):
                    return action

            # Wait until the right step to throw the error, and make sure we
            # only throw it once.
            if self.index < error_after or self.has_errored:
                self.index += 1
                return MessageAction(content=f'Test message {self.index}')

            ContextWindowExceededError(
                message='prompt is too long: 233885 tokens > 200000 maximum',
                model='',
                llm_provider='',
            )
            self.has_errored = True
            raise context_window_error

    step_state = StepState()
    mock_agent.step = step_state.step
    mock_agent.config = AgentConfig()

    # Because we're sending message actions, we need to respond to the recall
    # actions that get generated as a response.

    # We do that by playing the role of the recall module -- subscribe to the
    # event stream and respond to recall actions by inserting fake recall
    # observations.
    def on_event_memory(event: Event):
        if isinstance(event, RecallAction):
            microagent_obs = RecallObservation(
                content='Test microagent content',
                recall_type=RecallType.KNOWLEDGE,
            )
            microagent_obs._cause = event.id  # type: ignore
            test_event_stream.add_event(microagent_obs, EventSource.ENVIRONMENT)

    test_event_stream.subscribe(
        EventStreamSubscriber.MEMORY, on_event_memory, str(uuid4())
    )
    config = OpenHandsConfig(max_iterations=max_iterations)
    mock_runtime.event_stream = test_event_stream
    mock_runtime.config = copy.deepcopy(config)

    # Now we can run the controller for a fixed number of steps. Since the step
    # state is set to error out before then, if this terminates and we have a
    # record of the error being thrown we can be confident that the controller
    # handles the truncation correctly.
    # Mock the create_agent function to return our mock agent
    with patch('openhands.core.main.create_agent', return_value=mock_agent):
        final_state = await asyncio.wait_for(
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

    # Check that the context window exception was thrown and the controller
    # called the agent's `step` function the right number of times.
    assert step_state.has_errored
    assert len(step_state.views) == max_iterations - 1
    print('step_state.views: ', step_state.views)

    # Look at pre/post-step views. Normally, these should always increase in
    # size (because we return a message action, which triggers a recall, which
    # triggers a recall response). But if the pre/post-views are on the turn
    # when we throw the context window exceeded error, we should see the
    # post-step view compressed (condensation effects should be visible).
    for index, (first_view, second_view) in enumerate(
        zip(step_state.views[:-1], step_state.views[1:])
    ):
        if index == error_after:
            # Verify that no CondensationAction is present in either view
            # (CondensationAction events are never included in views)
            assert not any(isinstance(e, CondensationAction) for e in first_view.events)
            assert not any(
                isinstance(e, CondensationAction) for e in second_view.events
            )
            # The view length should be compressed due to condensation effects
            assert len(first_view) > len(second_view)
        else:
            # Before the error, the view length should increase
            assert len(first_view) < len(second_view)

    # The final state's history should contain:
    # - (max_iterations - 1) number of message actions (one iteration taken up with the condensation request)
    # - 1 recall actions,
    # - 1 recall observations,
    # - 1 condensation action.
    assert (
        len(
            [event for event in final_state.history if isinstance(event, MessageAction)]
        )
        == max_iterations - 1
    )
    assert (
        len(
            [
                event
                for event in final_state.history
                if isinstance(event, MessageAction)
                and event.source == EventSource.AGENT
            ]
        )
        == max_iterations - 2
    )
    assert (
        len([event for event in final_state.history if isinstance(event, RecallAction)])
        == 1
    )
    assert (
        len(
            [
                event
                for event in final_state.history
                if isinstance(event, RecallObservation)
            ]
        )
        == 1
    )
    assert (
        len(
            [
                event
                for event in final_state.history
                if isinstance(event, CondensationAction)
            ]
        )
        == 1
    )
    # With the refactored system message handling, we now have max_iterations + 4 events
    assert (
        len(final_state.history) == max_iterations + 4
    )  # 1 system message, 1 condensation action, 1 recall action, 1 recall observation

    assert len(final_state.view) == len(step_state.views[-1]) + 1

    # And these two representations of the state are _not_ the same.
    assert len(final_state.history) != len(final_state.view)