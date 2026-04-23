async def test_swarm_handoff(runtime: AgentRuntime | None) -> None:
    first_agent = _HandOffAgent("first_agent", description="first agent", next_agent="second_agent")
    second_agent = _HandOffAgent("second_agent", description="second agent", next_agent="third_agent")
    third_agent = _HandOffAgent("third_agent", description="third agent", next_agent="first_agent")

    termination = MaxMessageTermination(6)
    team = Swarm([second_agent, first_agent, third_agent], termination_condition=termination, runtime=runtime)
    result = await team.run(task="task")
    assert len(result.messages) == 6
    assert isinstance(result.messages[0], TextMessage)
    assert isinstance(result.messages[1], HandoffMessage)
    assert isinstance(result.messages[2], HandoffMessage)
    assert isinstance(result.messages[3], HandoffMessage)
    assert isinstance(result.messages[4], HandoffMessage)
    assert isinstance(result.messages[5], HandoffMessage)
    assert result.messages[0].content == "task"
    assert result.messages[1].content == "Transferred to third_agent."
    assert result.messages[2].content == "Transferred to first_agent."
    assert result.messages[3].content == "Transferred to second_agent."
    assert result.messages[4].content == "Transferred to third_agent."
    assert result.messages[5].content == "Transferred to first_agent."
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

    # Test save and load.
    state = await team.save_state()
    first_agent2 = _HandOffAgent("first_agent", description="first agent", next_agent="second_agent")
    second_agent2 = _HandOffAgent("second_agent", description="second agent", next_agent="third_agent")
    third_agent2 = _HandOffAgent("third_agent", description="third agent", next_agent="first_agent")
    team2 = Swarm([second_agent2, first_agent2, third_agent2], termination_condition=termination, runtime=runtime)
    await team2.load_state(state)
    state2 = await team2.save_state()
    assert state == state2
    manager_1 = await team._runtime.try_get_underlying_agent_instance(  # pyright: ignore
        AgentId(f"{team._group_chat_manager_name}_{team._team_id}", team._team_id),  # pyright: ignore
        SwarmGroupChatManager,  # pyright: ignore
    )  # pyright: ignore
    manager_2 = await team2._runtime.try_get_underlying_agent_instance(  # pyright: ignore
        AgentId(f"{team2._group_chat_manager_name}_{team2._team_id}", team2._team_id),  # pyright: ignore
        SwarmGroupChatManager,  # pyright: ignore
    )  # pyright: ignore
    assert manager_1._message_thread == manager_2._message_thread  # pyright: ignore
    assert manager_1._current_speaker == manager_2._current_speaker