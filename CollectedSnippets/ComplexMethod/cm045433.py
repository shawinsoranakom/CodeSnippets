async def test_round_robin_deeply_nested_teams(runtime: AgentRuntime | None) -> None:
    """Test RoundRobinGroupChat with deeply nested teams (3 levels)."""
    model_client = ReplayChatCompletionClient(
        [
            "Hello from agent1",
            "TERMINATE from agent2",
            "World from agent3",
            "Hello from agent1",
            "Hello from agent2",
            "TERMINATE from agent1",
            "TERMINATE from agent3",
            "Review from agent4",
            "TERMINATE from agent2",
            "TERMINATE from agent3",
            "TERMINATE from agent4",
        ]
    )

    # Create agents
    agent1 = AssistantAgent("agent1", model_client=model_client, description="First agent")
    agent2 = AssistantAgent("agent2", model_client=model_client, description="Second agent")
    agent3 = AssistantAgent("agent3", model_client=model_client, description="Third agent")
    agent4 = AssistantAgent("agent4", model_client=model_client, description="Fourth agent")

    # Create innermost team (level 1)
    innermost_team = RoundRobinGroupChat(
        participants=[agent1, agent2],
        termination_condition=TextMentionTermination("TERMINATE", sources=["agent1", "agent2"]),
        runtime=runtime,
        name="InnermostTeam",
    )

    # Create middle team (level 2)
    middle_team = RoundRobinGroupChat(
        participants=[innermost_team, agent3],
        termination_condition=TextMentionTermination("TERMINATE", sources=["agent3"]),
        runtime=runtime,
        name="MiddleTeam",
    )

    # Create outermost team (level 3)
    outermost_team = RoundRobinGroupChat(
        participants=[middle_team, agent4],
        termination_condition=TextMentionTermination("TERMINATE", sources=["agent4"]),
        runtime=runtime,
        name="OutermostTeam",
    )

    result: TaskResult | None = None
    async for msg in outermost_team.run_stream(task="Test deep nesting"):
        if isinstance(msg, TaskResult):
            result = msg
    assert result is not None
    # Should have task message + responses from each level
    assert len(result.messages) == 12
    assert isinstance(result.messages[0], TextMessage)
    assert result.messages[0].content == "Test deep nesting"
    assert result.stop_reason is not None and "TERMINATE" in result.stop_reason

    # Test component serialization of deeply nested structure
    config = outermost_team.dump_component()
    loaded_team = RoundRobinGroupChat.load_component(config)
    assert loaded_team.name == "OutermostTeam"

    # Verify nested structure is preserved
    loaded_config = loaded_team.dump_component()
    assert loaded_config == config