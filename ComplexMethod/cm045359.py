async def test_society_of_mind_agent_multiple_rounds(runtime: AgentRuntime | None) -> None:
    model_client = ReplayChatCompletionClient(
        ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
    )
    agent1 = AssistantAgent("assistant1", model_client=model_client, system_message="You are a helpful assistant.")
    agent2 = AssistantAgent("assistant2", model_client=model_client, system_message="You are a helpful assistant.")
    inner_termination = MaxMessageTermination(3)
    inner_team = RoundRobinGroupChat([agent1, agent2], termination_condition=inner_termination, runtime=runtime)
    society_of_mind_agent = SocietyOfMindAgent("society_of_mind", team=inner_team, model_client=model_client)
    response = await society_of_mind_agent.run(task="Count to 10.")
    assert len(response.messages) == 2
    assert response.messages[0].source == "user"
    assert response.messages[1].source == "society_of_mind"

    # Continue.
    response = await society_of_mind_agent.run()
    assert len(response.messages) == 1
    assert response.messages[0].source == "society_of_mind"

    # Continue.
    response = await society_of_mind_agent.run()
    assert len(response.messages) == 1
    assert response.messages[0].source == "society_of_mind"