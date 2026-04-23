async def test_default_output_task_messages_behavior() -> None:
    """Test that task messages are included by default (backward compatibility)."""
    # Create inner team
    model_client = ReplayChatCompletionClient(["Hello", "World", "TERMINATE"])
    agent1 = AssistantAgent("agent1", model_client=model_client)
    agent2 = AssistantAgent("agent2", model_client=model_client)
    termination = TextMentionTermination("TERMINATE")
    inner_team = RoundRobinGroupChat(participants=[agent1, agent2], termination_condition=termination)

    streamed_messages: List[BaseAgentEvent | BaseChatMessage] = []
    final_result: TaskResult | None = None

    # Test default behavior (should include task messages since default is True)
    async for message in inner_team.run_stream(task="Test default behavior"):
        if isinstance(message, TaskResult):
            final_result = message
        else:
            streamed_messages.append(message)

    # Verify default behavior: task message should be included in stream
    assert final_result is not None
    task_message_found_in_stream = any(
        isinstance(msg, TextMessage) and msg.source == "user" and "Test default behavior" in msg.content
        for msg in streamed_messages
    )
    assert task_message_found_in_stream, "Task message should be included in stream by default"

    # Validate that task message is included in the TaskResult.messages by default
    task_message_in_result = any(
        isinstance(msg, TextMessage) and msg.source == "user" and "Test default behavior" in msg.content
        for msg in final_result.messages
    )
    assert task_message_in_result, "Task message should be included in TaskResult.messages by default"

    # Verify the content structure makes sense (task message + agent responses)
    user_messages = [msg for msg in final_result.messages if isinstance(msg, TextMessage) and msg.source == "user"]
    agent_messages = [
        msg for msg in final_result.messages if isinstance(msg, TextMessage) and msg.source in ["agent1", "agent2"]
    ]

    assert len(user_messages) >= 1, "Should have at least one user message (the task)"
    assert len(agent_messages) >= 1, "Should have at least one agent response"
    assert user_messages[0].content == "Test default behavior", "First user message should be the task"