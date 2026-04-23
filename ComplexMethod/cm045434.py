async def test_selector_deeply_nested_teams(runtime: AgentRuntime | None) -> None:
    """Test SelectorGroupChat with deeply nested teams (3 levels)."""
    model_client_inner = ReplayChatCompletionClient(
        [
            "Hello from innermost agent 1",
            "Hello from innermost agent 2",
            "TERMINATE from innermost agent 1",
        ]
    )
    model_client_middle = ReplayChatCompletionClient(
        [
            "InnermostTeam",  # Select innermost team
            "TERMINATE from agent3",
        ]
    )
    model_client_outter = ReplayChatCompletionClient(
        [
            "MiddleTeam",  # Select middle team
            "agent4",  # Select agent4
            "Hello from outermost agent 4",
            "agent4",  # Select agent4 again
            "TERMINATE from agent4",
        ]
    )

    # Create agents
    agent1 = AssistantAgent("agent1", model_client=model_client_inner, description="First agent")
    agent2 = AssistantAgent("agent2", model_client=model_client_inner, description="Second agent")
    agent3 = AssistantAgent("agent3", model_client=model_client_middle, description="Third agent")
    agent4 = AssistantAgent("agent4", model_client=model_client_outter, description="Fourth agent")

    # Create innermost team (level 1) - RoundRobin for simplicity
    innermost_team = RoundRobinGroupChat(
        participants=[agent1, agent2],
        termination_condition=TextMentionTermination("TERMINATE", sources=["agent1", "agent2"]),
        runtime=runtime,
        name="InnermostTeam",
    )

    # Create middle team (level 2) - Selector
    middle_team = SelectorGroupChat(
        participants=[innermost_team, agent3],
        model_client=model_client_middle,
        termination_condition=TextMentionTermination("TERMINATE", sources=["agent3"]),
        runtime=runtime,
        name="MiddleTeam",
    )

    # Create outermost team (level 3) - Selector
    outermost_team = SelectorGroupChat(
        participants=[middle_team, agent4],
        model_client=model_client_outter,
        termination_condition=TextMentionTermination("TERMINATE", sources=["agent4"]),
        runtime=runtime,
        name="OutermostTeam",
        allow_repeated_speaker=True,
    )

    result: TaskResult | None = None
    async for msg in outermost_team.run_stream(task="Test deep nesting"):
        if isinstance(msg, TaskResult):
            result = msg
    assert result is not None

    # Should have task message + selector events + responses from each level
    assert len(result.messages) == 7
    assert isinstance(result.messages[0], TextMessage)
    assert result.messages[0].content == "Test deep nesting"
    assert result.stop_reason is not None and "TERMINATE" in result.stop_reason

    # Test component serialization of deeply nested structure
    config = outermost_team.dump_component()
    loaded_team = SelectorGroupChat.load_component(config)
    assert loaded_team.name == "OutermostTeam"

    # Verify nested structure is preserved
    loaded_config = loaded_team.dump_component()
    assert loaded_config == config