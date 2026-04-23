async def test_swarm_pause_and_resume(runtime: AgentRuntime | None) -> None:
    first_agent = _HandOffAgent("first_agent", description="first agent", next_agent="second_agent")
    second_agent = _HandOffAgent("second_agent", description="second agent", next_agent="third_agent")
    third_agent = _HandOffAgent("third_agent", description="third agent", next_agent="first_agent")

    team = Swarm([second_agent, first_agent, third_agent], max_turns=1, runtime=runtime)
    result = await team.run(task="task")
    assert len(result.messages) == 2
    assert isinstance(result.messages[0], TextMessage)
    assert isinstance(result.messages[1], HandoffMessage)
    assert result.messages[0].content == "task"
    assert result.messages[1].content == "Transferred to third_agent."

    # Resume with a new task.
    result = await team.run(task="new task")
    assert len(result.messages) == 2
    assert isinstance(result.messages[0], TextMessage)
    assert isinstance(result.messages[1], HandoffMessage)
    assert result.messages[0].content == "new task"
    assert result.messages[1].content == "Transferred to first_agent."

    # Resume with the same task.
    result = await team.run()
    assert len(result.messages) == 1
    assert isinstance(result.messages[0], HandoffMessage)
    assert result.messages[0].content == "Transferred to second_agent."