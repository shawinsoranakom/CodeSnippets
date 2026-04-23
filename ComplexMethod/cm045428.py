async def test_selector_group_chat_streaming(runtime: AgentRuntime | None) -> None:
    model_client = ReplayChatCompletionClient(
        ["the agent should be agent2"],
    )
    agent2 = _StopAgent("agent2", description="stop agent 2", stop_at=0)
    agent3 = _EchoAgent("agent3", description="echo agent 3")
    termination = StopMessageTermination()
    team = SelectorGroupChat(
        participants=[agent2, agent3],
        model_client=model_client,
        termination_condition=termination,
        runtime=runtime,
        emit_team_events=True,
        model_client_streaming=True,
    )
    result = await team.run(
        task="Write a program that prints 'Hello, world!'",
    )

    assert len(result.messages) == 4
    assert isinstance(result.messages[0], TextMessage)
    assert isinstance(result.messages[1], SelectorEvent)
    assert isinstance(result.messages[2], SelectSpeakerEvent)
    assert isinstance(result.messages[3], StopMessage)

    assert result.messages[0].content == "Write a program that prints 'Hello, world!'"
    assert result.messages[1].content == "the agent should be agent2"
    assert result.messages[2].content == ["agent2"]
    assert result.messages[3].source == "agent2"
    assert result.stop_reason is not None and result.stop_reason == "Stop message received"

    # Test streaming
    await team.reset()
    model_client.reset()
    result_index = 0  # Include task message in result since output_task_messages=True by default
    streamed_chunks: List[str] = []
    final_result: TaskResult | None = None
    async for message in team.run_stream(
        task="Write a program that prints 'Hello, world!'",
    ):
        if isinstance(message, TaskResult):
            final_result = message
            assert compare_task_results(message, result)
        elif isinstance(message, ModelClientStreamingChunkEvent):
            streamed_chunks.append(message.content)
        else:
            if streamed_chunks:
                assert isinstance(message, SelectorEvent)
                assert message.content == "".join(streamed_chunks)
                streamed_chunks = []
            assert compare_messages(message, result.messages[result_index])
            result_index += 1

    # Verify we got the expected messages without relying on fragile ordering
    assert final_result is not None
    assert len(streamed_chunks) == 0