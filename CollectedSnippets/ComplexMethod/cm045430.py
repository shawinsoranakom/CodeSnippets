async def test_round_robin_group_chat_nested_teams_dump_load_component(runtime: AgentRuntime | None) -> None:
    """Test RoundRobinGroupChat with nested teams dump_component and load_component."""
    model_client = ReplayChatCompletionClient(["Hello from agent1", "Hello from agent2", "Hello from agent3"])

    # Create agents
    agent1 = AssistantAgent("agent1", model_client=model_client, description="First agent")
    agent2 = AssistantAgent("agent2", model_client=model_client, description="Second agent")
    agent3 = AssistantAgent("agent3", model_client=model_client, description="Third agent")
    termination = MaxMessageTermination(2)

    # Create inner team
    inner_team = RoundRobinGroupChat(
        participants=[agent1, agent2],
        termination_condition=termination,
        runtime=runtime,
        name="InnerTeam",
        description="Inner team description",
    )

    # Create outer team with nested inner team
    outer_team = RoundRobinGroupChat(
        participants=[inner_team, agent3],
        termination_condition=termination,
        runtime=runtime,
        name="OuterTeam",
        description="Outer team description",
    )

    # Test dump_component
    config = outer_team.dump_component()
    assert config.config["name"] == "OuterTeam"
    assert config.config["description"] == "Outer team description"
    assert len(config.config["participants"]) == 2

    # First participant should be the inner team
    inner_team_config = config.config["participants"][0]["config"]
    assert inner_team_config["name"] == "InnerTeam"
    assert inner_team_config["description"] == "Inner team description"
    assert len(inner_team_config["participants"]) == 2

    # Second participant should be agent3
    agent3_config = config.config["participants"][1]["config"]
    assert agent3_config["name"] == "agent3"

    # Test load_component
    loaded_team = RoundRobinGroupChat.load_component(config)
    assert loaded_team.name == "OuterTeam"
    assert loaded_team.description == "Outer team description"
    assert len(loaded_team._participants) == 2  # type: ignore[reportPrivateUsage]

    # Verify the loaded team has the same structure
    loaded_config = loaded_team.dump_component()
    assert loaded_config == config