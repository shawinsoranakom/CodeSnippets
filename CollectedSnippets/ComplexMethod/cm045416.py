async def test_selector_group_chat_two_speakers(runtime: AgentRuntime | None) -> None:
    model_client = ReplayChatCompletionClient(["agent2"])

    agent1 = _StopAgent("agent1", description="echo agent 1", stop_at=2)
    agent2 = _EchoAgent("agent2", description="echo agent 2")
    termination = TextMentionTermination("TERMINATE")
    team = SelectorGroupChat(
        participants=[agent1, agent2],
        termination_condition=termination,
        model_client=model_client,
        runtime=runtime,
    )
    result = await team.run(
        task="Write a program that prints 'Hello, world!'",
    )
    assert len(result.messages) == 5
    assert isinstance(result.messages[0], TextMessage)
    assert result.messages[0].content == "Write a program that prints 'Hello, world!'"
    assert result.messages[1].source == "agent2"
    assert result.messages[2].source == "agent1"
    assert result.messages[3].source == "agent2"
    assert result.messages[4].source == "agent1"
    assert result.stop_reason is not None and result.stop_reason == "Text 'TERMINATE' mentioned"

    # Test streaming.
    model_client.reset()
    agent1._count = 0  # pyright: ignore
    result_index = 0  # Include task message in result since output_task_messages=True by default
    await team.reset()
    async for message in team.run_stream(task="Write a program that prints 'Hello, world!'"):
        if isinstance(message, TaskResult):
            assert compare_task_results(message, result)
        else:
            assert compare_messages(message, result.messages[result_index])
            result_index += 1

    # Test Console.
    model_client.reset()
    agent1._count = 0  # pyright: ignore
    await team.reset()
    result2 = await Console(team.run_stream(task="Write a program that prints 'Hello, world!'"))
    assert compare_task_results(result2, result)