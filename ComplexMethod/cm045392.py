async def test_digraph_group_chat_sequential_execution(runtime: AgentRuntime | None) -> None:
    # Create agents A → B → C
    agent_a = _EchoAgent("A", description="Echo agent A")
    agent_b = _EchoAgent("B", description="Echo agent B")
    agent_c = _EchoAgent("C", description="Echo agent C")

    # Define graph A → B → C
    graph = DiGraph(
        nodes={
            "A": DiGraphNode(name="A", edges=[DiGraphEdge(target="B")]),
            "B": DiGraphNode(name="B", edges=[DiGraphEdge(target="C")]),
            "C": DiGraphNode(name="C", edges=[]),
        }
    )

    # Create team using Graph
    team = GraphFlow(
        participants=[agent_a, agent_b, agent_c],
        graph=graph,
        runtime=runtime,
        termination_condition=MaxMessageTermination(5),
    )

    # Run the chat
    result: TaskResult = await team.run(task="Hello from User")

    assert len(result.messages) == 4
    assert isinstance(result.messages[0], TextMessage)
    assert result.messages[0].source == "user"
    assert result.messages[1].source == "A"
    assert result.messages[2].source == "B"
    assert result.messages[3].source == "C"
    assert all(isinstance(m, TextMessage) for m in result.messages)
    assert result.stop_reason is not None