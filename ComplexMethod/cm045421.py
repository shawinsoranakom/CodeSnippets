async def test_swarm_handoff_with_team_events(runtime: AgentRuntime | None) -> None:
    first_agent = _HandOffAgent("first_agent", description="first agent", next_agent="second_agent")
    second_agent = _HandOffAgent("second_agent", description="second agent", next_agent="third_agent")
    third_agent = _HandOffAgent("third_agent", description="third agent", next_agent="first_agent")

    termination = MaxMessageTermination(6)
    team = Swarm(
        [second_agent, first_agent, third_agent],
        termination_condition=termination,
        runtime=runtime,
        emit_team_events=True,
    )
    result = await team.run(task="task")
    assert len(result.messages) == 11
    assert isinstance(result.messages[0], TextMessage)
    assert isinstance(result.messages[1], SelectSpeakerEvent)
    assert isinstance(result.messages[2], HandoffMessage)
    assert isinstance(result.messages[3], SelectSpeakerEvent)
    assert isinstance(result.messages[4], HandoffMessage)
    assert isinstance(result.messages[5], SelectSpeakerEvent)
    assert isinstance(result.messages[6], HandoffMessage)
    assert isinstance(result.messages[7], SelectSpeakerEvent)
    assert isinstance(result.messages[8], HandoffMessage)
    assert isinstance(result.messages[9], SelectSpeakerEvent)
    assert isinstance(result.messages[10], HandoffMessage)
    assert result.messages[0].content == "task"
    assert result.messages[1].content == ["second_agent"]
    assert result.messages[2].content == "Transferred to third_agent."
    assert result.messages[3].content == ["third_agent"]
    assert result.messages[4].content == "Transferred to first_agent."
    assert result.messages[5].content == ["first_agent"]
    assert result.messages[6].content == "Transferred to second_agent."
    assert result.messages[7].content == ["second_agent"]
    assert result.messages[8].content == "Transferred to third_agent."
    assert result.messages[9].content == ["third_agent"]
    assert result.messages[10].content == "Transferred to first_agent."
    assert (
        result.stop_reason is not None
        and result.stop_reason == "Maximum number of messages 6 reached, current message count: 6"
    )

    # Test streaming.
    result_index = 0  # Include task message in result since output_task_messages=True by default
    await team.reset()
    stream = team.run_stream(task="task")
    async for message in stream:
        if isinstance(message, TaskResult):
            assert compare_task_results(message, result)
        else:
            assert compare_messages(message, result.messages[result_index])
            result_index += 1