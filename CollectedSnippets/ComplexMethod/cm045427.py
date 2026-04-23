async def test_declarative_groupchats_with_config(runtime: AgentRuntime | None) -> None:
    # Create basic agents and components for testing
    agent1 = AssistantAgent(
        "agent_1",
        model_client=OpenAIChatCompletionClient(model="gpt-4.1-nano-2025-04-14", api_key=""),
        handoffs=["agent_2"],
    )
    agent2 = AssistantAgent(
        "agent_2", model_client=OpenAIChatCompletionClient(model="gpt-4.1-nano-2025-04-14", api_key="")
    )
    termination = MaxMessageTermination(4)
    model_client = OpenAIChatCompletionClient(model="gpt-4.1-nano-2025-04-14", api_key="")

    # Test round robin - verify config is preserved
    round_robin = RoundRobinGroupChat(participants=[agent1, agent2], termination_condition=termination, max_turns=5)
    config = round_robin.dump_component()
    loaded = RoundRobinGroupChat.load_component(config)
    assert loaded.dump_component() == config

    # Test selector group chat - verify config is preserved
    selector_prompt = "Custom selector prompt with {roles}, {participants}, {history}"
    selector = SelectorGroupChat(
        participants=[agent1, agent2],
        model_client=model_client,
        termination_condition=termination,
        max_turns=10,
        selector_prompt=selector_prompt,
        allow_repeated_speaker=True,
        runtime=runtime,
    )
    selector_config = selector.dump_component()
    selector_loaded = SelectorGroupChat.load_component(selector_config)
    assert selector_loaded.dump_component() == selector_config

    # Test swarm with handoff termination
    handoff_termination = HandoffTermination(target="Agent2")
    swarm = Swarm(
        participants=[agent1, agent2], termination_condition=handoff_termination, max_turns=5, runtime=runtime
    )
    swarm_config = swarm.dump_component()
    swarm_loaded = Swarm.load_component(swarm_config)
    assert swarm_loaded.dump_component() == swarm_config

    # Test MagenticOne with custom parameters
    magentic = MagenticOneGroupChat(
        participants=[agent1],
        model_client=model_client,
        max_turns=15,
        max_stalls=5,
        final_answer_prompt="Custom prompt",
        runtime=runtime,
    )
    magentic_config = magentic.dump_component()
    magentic_loaded = MagenticOneGroupChat.load_component(magentic_config)
    assert magentic_loaded.dump_component() == magentic_config

    # Verify component types are correctly set for each
    for team in [loaded, selector, swarm, magentic]:
        assert team.component_type == "team"

    # Verify provider strings are correctly set
    assert round_robin.dump_component().provider == "autogen_agentchat.teams.RoundRobinGroupChat"
    assert selector.dump_component().provider == "autogen_agentchat.teams.SelectorGroupChat"
    assert swarm.dump_component().provider == "autogen_agentchat.teams.Swarm"
    assert magentic.dump_component().provider == "autogen_agentchat.teams.MagenticOneGroupChat"