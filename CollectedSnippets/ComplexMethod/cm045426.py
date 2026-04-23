async def test_round_robin_group_chat_with_message_list(runtime: AgentRuntime | None) -> None:
    # Create a simple team with echo agents
    agent1 = _EchoAgent("Agent1", "First agent")
    agent2 = _EchoAgent("Agent2", "Second agent")
    termination = MaxMessageTermination(4)  # Stop after 4 messages
    team = RoundRobinGroupChat([agent1, agent2], termination_condition=termination, runtime=runtime)

    # Create a list of messages
    messages: List[BaseChatMessage] = [
        TextMessage(content="Message 1", source="user"),
        TextMessage(content="Message 2", source="user"),
        TextMessage(content="Message 3", source="user"),
    ]

    # Run the team with the message list
    result = await team.run(task=messages)

    # Verify the messages were processed in order
    assert len(result.messages) == 4  # Initial messages + echo until termination
    assert isinstance(result.messages[0], TextMessage)
    assert isinstance(result.messages[1], TextMessage)
    assert isinstance(result.messages[2], TextMessage)
    assert isinstance(result.messages[3], TextMessage)
    assert result.messages[0].content == "Message 1"  # First message
    assert result.messages[1].content == "Message 2"  # Second message
    assert result.messages[2].content == "Message 3"  # Third message
    assert result.messages[3].content == "Message 1"  # Echo from first agent
    assert result.stop_reason == "Maximum number of messages 4 reached, current message count: 4"

    # Test with streaming
    await team.reset()
    result_index = 0  # Include the 3 task messages in result since output_task_messages=True by default
    async for message in team.run_stream(task=messages):
        if isinstance(message, TaskResult):
            assert compare_task_results(message, result)
        else:
            assert compare_messages(message, result.messages[result_index])
            result_index += 1

    # Test with invalid message list
    with pytest.raises(ValueError, match="All messages in task list must be valid BaseChatMessage types"):
        await team.run(task=["not a message"])  # type: ignore[list-item, arg-type]  # intentionally testing invalid input

    # Test with empty message list
    with pytest.raises(ValueError, match="Task list cannot be empty"):
        await team.run(task=[])