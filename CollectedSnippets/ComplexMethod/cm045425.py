async def test_swarm_with_handoff_termination(runtime: AgentRuntime | None) -> None:
    first_agent = _HandOffAgent("first_agent", description="first agent", next_agent="second_agent")
    second_agent = _HandOffAgent("second_agent", description="second agent", next_agent="third_agent")
    third_agent = _HandOffAgent("third_agent", description="third agent", next_agent="first_agent")

    # Handoff to an existing agent.
    termination = HandoffTermination(target="third_agent")
    team = Swarm([second_agent, first_agent, third_agent], termination_condition=termination, runtime=runtime)
    # Start
    result = await team.run(task="task")
    assert len(result.messages) == 2
    assert isinstance(result.messages[0], TextMessage)
    assert isinstance(result.messages[1], HandoffMessage)
    assert result.messages[0].content == "task"
    assert result.messages[1].content == "Transferred to third_agent."
    # Resume existing.
    result = await team.run()
    assert len(result.messages) == 3
    assert isinstance(result.messages[0], HandoffMessage)
    assert isinstance(result.messages[1], HandoffMessage)
    assert isinstance(result.messages[2], HandoffMessage)
    assert result.messages[0].content == "Transferred to first_agent."
    assert result.messages[1].content == "Transferred to second_agent."
    assert result.messages[2].content == "Transferred to third_agent."
    # Resume new task.
    result = await team.run(task="new task")
    assert len(result.messages) == 4
    assert isinstance(result.messages[0], TextMessage)
    assert isinstance(result.messages[1], HandoffMessage)
    assert isinstance(result.messages[2], HandoffMessage)
    assert isinstance(result.messages[3], HandoffMessage)
    assert result.messages[0].content == "new task"
    assert result.messages[1].content == "Transferred to first_agent."
    assert result.messages[2].content == "Transferred to second_agent."
    assert result.messages[3].content == "Transferred to third_agent."

    # Handoff to a non-existing agent.
    third_agent = _HandOffAgent("third_agent", description="third agent", next_agent="non_existing_agent")
    termination = HandoffTermination(target="non_existing_agent")
    team = Swarm([second_agent, first_agent, third_agent], termination_condition=termination, runtime=runtime)
    # Start
    result = await team.run(task="task")
    assert len(result.messages) == 3
    assert isinstance(result.messages[0], TextMessage)
    assert isinstance(result.messages[1], HandoffMessage)
    assert isinstance(result.messages[2], HandoffMessage)
    assert result.messages[0].content == "task"
    assert result.messages[1].content == "Transferred to third_agent."
    assert result.messages[2].content == "Transferred to non_existing_agent."
    # Attempt to resume.
    with pytest.raises(ValueError):
        await team.run()
    # Attempt to resume with a new task.
    with pytest.raises(ValueError):
        await team.run(task="new task")
    # Resume with a HandoffMessage
    result = await team.run(task=HandoffMessage(content="Handoff to first_agent.", target="first_agent", source="user"))
    assert len(result.messages) == 4
    assert isinstance(result.messages[0], HandoffMessage)
    assert isinstance(result.messages[1], HandoffMessage)
    assert isinstance(result.messages[2], HandoffMessage)
    assert isinstance(result.messages[3], HandoffMessage)
    assert result.messages[0].content == "Handoff to first_agent."
    assert result.messages[1].content == "Transferred to second_agent."
    assert result.messages[2].content == "Transferred to third_agent."
    assert result.messages[3].content == "Transferred to non_existing_agent."