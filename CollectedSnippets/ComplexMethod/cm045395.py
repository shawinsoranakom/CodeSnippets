async def test_digraph_group_chat_chained_parallel_join_any(runtime: AgentRuntime | None) -> None:
    agent_a = _EchoAgent("A", description="Echo agent A")
    agent_b = _EchoAgent("B", description="Echo agent B")
    agent_c = _EchoAgent("C", description="Echo agent C")
    agent_d = _EchoAgent("D", description="Echo agent D")
    agent_e = _EchoAgent("E", description="Echo agent E")

    graph = DiGraph(
        nodes={
            "A": DiGraphNode(name="A", edges=[DiGraphEdge(target="B"), DiGraphEdge(target="C")]),
            "B": DiGraphNode(name="B", edges=[DiGraphEdge(target="D")]),
            "C": DiGraphNode(name="C", edges=[DiGraphEdge(target="D")]),
            "D": DiGraphNode(name="D", edges=[DiGraphEdge(target="E")], activation="any"),
            "E": DiGraphNode(name="E", edges=[], activation="any"),
        }
    )

    team = GraphFlow(
        participants=[agent_a, agent_b, agent_c, agent_d, agent_e],
        graph=graph,
        runtime=runtime,
        termination_condition=MaxMessageTermination(20),
    )

    result = await team.run(task="Run chained parallel join-any")

    sequence = [msg.source for msg in result.messages if isinstance(msg, TextMessage)]

    # D should trigger twice
    d_indices = [i for i, s in enumerate(sequence) if s == "D"]
    assert len(d_indices) == 1
    # Each D trigger must be after corresponding B or C
    b_index = sequence.index("B")
    c_index = sequence.index("C")
    assert any(d > b_index for d in d_indices)
    assert any(d > c_index for d in d_indices)

    # E should also trigger twice → once after each D
    e_indices = [i for i, s in enumerate(sequence) if s == "E"]
    assert len(e_indices) == 1
    assert e_indices[0] > d_indices[0]
    assert result.stop_reason is not None