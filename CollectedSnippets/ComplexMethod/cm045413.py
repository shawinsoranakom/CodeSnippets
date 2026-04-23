async def test_round_robin_group_chat_max_turn(runtime: AgentRuntime | None) -> None:
    agent_1 = _EchoAgent("agent_1", description="echo agent 1")
    agent_2 = _EchoAgent("agent_2", description="echo agent 2")
    agent_3 = _EchoAgent("agent_3", description="echo agent 3")
    agent_4 = _EchoAgent("agent_4", description="echo agent 4")
    team = RoundRobinGroupChat(participants=[agent_1, agent_2, agent_3, agent_4], max_turns=3, runtime=runtime)
    result = await team.run(
        task="Write a program that prints 'Hello, world!'",
    )
    assert len(result.messages) == 4
    assert result.messages[1].source == "agent_1"
    assert result.messages[2].source == "agent_2"
    assert result.messages[3].source == "agent_3"
    assert result.stop_reason is not None

    # Resume.
    result = await team.run()
    assert len(result.messages) == 3
    assert result.messages[0].source == "agent_4"
    assert result.messages[1].source == "agent_1"
    assert result.messages[2].source == "agent_2"
    assert result.stop_reason is not None

    # Reset.
    await team.reset()
    result = await team.run(task="Write a program that prints 'Hello, world!'")
    assert len(result.messages) == 4
    assert result.messages[1].source == "agent_1"
    assert result.messages[2].source == "agent_2"
    assert result.messages[3].source == "agent_3"
    assert result.stop_reason is not None