async def test_society_of_mind_agent_output_task_messages_parameter(runtime: AgentRuntime | None) -> None:
    """Test that output_task_messages parameter controls whether task messages are included in the stream."""
    model_client = ReplayChatCompletionClient(
        ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
    )
    agent1 = AssistantAgent("assistant1", model_client=model_client, system_message="You are a helpful assistant.")
    agent2 = AssistantAgent("assistant2", model_client=model_client, system_message="You are a helpful assistant.")
    inner_termination = MaxMessageTermination(2)  # Reduce to 2 to use fewer responses
    inner_team = RoundRobinGroupChat([agent1, agent2], termination_condition=inner_termination, runtime=runtime)

    # Test 1: Test team with output_task_messages=True (default behavior)
    messages_with_task: List[BaseAgentEvent | BaseChatMessage] = []
    async for message in inner_team.run_stream(task="Count to 10", output_task_messages=True):
        if not isinstance(message, TaskResult):
            messages_with_task.append(message)

    # Should include the task message
    assert len(messages_with_task) >= 1
    assert any(
        isinstance(msg, TextMessage) and msg.source == "user" and "Count to 10" in msg.content
        for msg in messages_with_task
    )

    # Reset team before next test
    await inner_team.reset()

    # Test 2: Test team with output_task_messages=False
    messages_without_task: List[BaseAgentEvent | BaseChatMessage] = []
    async for message in inner_team.run_stream(task="Count to 10", output_task_messages=False):
        if not isinstance(message, TaskResult):
            messages_without_task.append(message)

    # Should NOT include the task message in the stream
    assert not any(
        isinstance(msg, TextMessage) and msg.source == "user" and "Count to 10" in msg.content
        for msg in messages_without_task
    )

    # Reset team before next test
    await inner_team.reset()

    # Test 3: Test SocietyOfMindAgent uses output_task_messages=False internally
    # Create a separate model client for SocietyOfMindAgent to ensure we have enough responses
    soma_model_client = ReplayChatCompletionClient(
        ["Final response from society of mind"],
    )
    society_of_mind_agent = SocietyOfMindAgent("society_of_mind", team=inner_team, model_client=soma_model_client)

    # Collect all messages from the SocietyOfMindAgent stream
    soma_messages: List[BaseAgentEvent | BaseChatMessage] = []
    async for message in society_of_mind_agent.run_stream(task="Count to 10"):
        if not isinstance(message, TaskResult):
            soma_messages.append(message)

    # The SocietyOfMindAgent should output the task message (since it's the outer agent)
    # but should NOT forward the task messages from its inner team
    task_messages_in_soma = [msg for msg in soma_messages if isinstance(msg, TextMessage) and msg.source == "user"]

    # Count how many times "Count to 10" appears in the stream
    # With proper implementation, it should appear exactly once (from outer level only)
    count_task_messages = sum(
        1
        for msg in soma_messages
        if isinstance(msg, TextMessage) and msg.source == "user" and "Count to 10" in msg.content
    )

    # Should have exactly one task message (from the outer level only)
    assert len(task_messages_in_soma) == 1
    assert count_task_messages == 1  # Should appear exactly once, not duplicated from inner team

    # Should have the SocietyOfMindAgent's final response
    soma_responses = [msg for msg in soma_messages if isinstance(msg, TextMessage) and msg.source == "society_of_mind"]
    assert len(soma_responses) == 1