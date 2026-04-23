async def test_selector_group_chat_with_team_event(runtime: AgentRuntime | None) -> None:
    model_client = ReplayChatCompletionClient(
        ["agent3", "agent2", "agent1", "agent2", "agent1"],
    )
    agent1 = _StopAgent("agent1", description="echo agent 1", stop_at=2)
    agent2 = _EchoAgent("agent2", description="echo agent 2")
    agent3 = _EchoAgent("agent3", description="echo agent 3")
    termination = TextMentionTermination("TERMINATE")
    team = SelectorGroupChat(
        participants=[agent1, agent2, agent3],
        model_client=model_client,
        termination_condition=termination,
        runtime=runtime,
        emit_team_events=True,
    )
    result = await team.run(
        task="Write a program that prints 'Hello, world!'",
    )
    assert len(result.messages) == 11
    assert isinstance(result.messages[0], TextMessage)
    assert isinstance(result.messages[1], SelectSpeakerEvent)
    assert isinstance(result.messages[2], TextMessage)
    assert isinstance(result.messages[3], SelectSpeakerEvent)
    assert isinstance(result.messages[4], TextMessage)
    assert isinstance(result.messages[5], SelectSpeakerEvent)
    assert isinstance(result.messages[6], TextMessage)
    assert isinstance(result.messages[7], SelectSpeakerEvent)
    assert isinstance(result.messages[8], TextMessage)
    assert isinstance(result.messages[9], SelectSpeakerEvent)
    assert isinstance(result.messages[10], StopMessage)
    assert result.messages[0].content == "Write a program that prints 'Hello, world!'"
    assert result.messages[1].content == ["agent3"]
    assert result.messages[2].source == "agent3"
    assert result.messages[3].content == ["agent2"]
    assert result.messages[4].source == "agent2"
    assert result.messages[5].content == ["agent1"]
    assert result.messages[6].source == "agent1"
    assert result.messages[7].content == ["agent2"]
    assert result.messages[8].source == "agent2"
    assert result.messages[9].content == ["agent1"]
    assert result.messages[10].source == "agent1"
    assert result.stop_reason is not None and result.stop_reason == "Text 'TERMINATE' mentioned"

    # Test streaming.
    model_client.reset()
    agent1._count = 0  # pyright: ignore
    result_index = 0  # Include task message in result since output_task_messages=True by default
    await team.reset()
    async for message in team.run_stream(
        task="Write a program that prints 'Hello, world!'",
    ):
        if isinstance(message, TaskResult):
            assert compare_task_results(message, result)
        else:
            assert compare_messages(message, result.messages[result_index])
            result_index += 1