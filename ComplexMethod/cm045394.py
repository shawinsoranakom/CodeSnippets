async def test_digraph_group_chat_parallel_join_any_1(runtime: AgentRuntime | None) -> None:
    agent_a = _EchoAgent("A", description="Echo agent A")
    agent_b = _EchoAgent("B", description="Echo agent B")
    agent_c = _EchoAgent("C", description="Echo agent C")
    agent_d = _EchoAgent("D", description="Echo agent D")

    graph = DiGraph(
        nodes={
            "A": DiGraphNode(name="A", edges=[DiGraphEdge(target="B"), DiGraphEdge(target="C")]),
            "B": DiGraphNode(name="B", edges=[DiGraphEdge(target="D", activation_group="any")]),
            "C": DiGraphNode(name="C", edges=[DiGraphEdge(target="D", activation_group="any")]),
            "D": DiGraphNode(name="D", edges=[]),
        }
    )

    team = GraphFlow(
        participants=[agent_a, agent_b, agent_c, agent_d],
        graph=graph,
        runtime=runtime,
        termination_condition=MaxMessageTermination(10),
    )

    result = await team.run(task="Run parallel join")
    sequence = [msg.source for msg in result.messages if isinstance(msg, TextMessage)]
    assert sequence[0] == "user"
    # B and C should both run
    assert "B" in sequence
    assert "C" in sequence
    # D should trigger twice → once after B and once after C (order depends on runtime)
    d_indices = [i for i, s in enumerate(sequence) if s == "D"]
    assert len(d_indices) == 1
    # Each D trigger must be after corresponding B or C
    b_index = sequence.index("B")
    c_index = sequence.index("C")
    assert any(d > b_index for d in d_indices)
    assert any(d > c_index for d in d_indices)
    assert result.stop_reason is not None