async def test_tool_call_validation_error_handling(
    mock_agent_with_stats,
    test_event_stream,
):
    """Test that tool call validation errors from Groq are handled as recoverable errors."""
    mock_agent, conversation_stats, llm_registry = mock_agent_with_stats

    controller = AgentController(
        agent=mock_agent,
        event_stream=test_event_stream,
        conversation_stats=conversation_stats,
        iteration_delta=10,
        sid='test',
        confirmation_mode=False,
        headless_mode=True,
    )

    controller.state.agent_state = AgentState.RUNNING

    # Track call count to only raise error on first call
    # This prevents a feedback loop where ErrorObservation triggers another step
    # which raises the same error again (since the mock always raises)
    call_count = 0

    def mock_step(state):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise BadRequestError(
                message='litellm.BadRequestError: GroqException - {"error":{"message":"tool call validation failed: parameters for tool str_replace_editor did not match schema: errors: [missing properties: \'path\']","type":"invalid_request_error","code":"tool_use_failed"}}',
                model='groq/llama3-8b-8192',
                llm_provider='groq',
            )
        # Return NullAction on subsequent calls to break the feedback loop
        return NullAction()

    mock_agent.step = mock_step

    # Call _step which should handle the tool validation error
    await controller._step()

    # Verify that the agent state is still RUNNING (not ERROR)
    assert controller.state.agent_state == AgentState.RUNNING

    # Verify that an ErrorObservation was added to the event stream
    events = list(test_event_stream.get_events())
    error_observations = [e for e in events if isinstance(e, ErrorObservation)]
    assert len(error_observations) == 1

    error_obs = error_observations[0]
    assert 'tool call validation failed' in error_obs.content
    assert 'missing properties' in error_obs.content
    assert 'path' in error_obs.content

    await controller.close()