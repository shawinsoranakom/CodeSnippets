def test_build_conditional_loop() -> None:
    client = ReplayChatCompletionClient(["loop", "loop", "exit"])
    a = AssistantAgent("A", model_client=client)
    b = AssistantAgent("B", model_client=client)
    c = AssistantAgent("C", model_client=client)

    builder = DiGraphBuilder()
    builder.add_node(a).add_node(b).add_node(c)
    builder.add_edge(a, b)
    builder.add_conditional_edges(b, {"loop": a, "exit": c})
    builder.set_entry_point(a)
    graph = builder.build()

    # Check that edges have the right conditions and targets
    edges = graph.nodes["B"].edges
    assert len(edges) == 2

    # Find edges by their conditions
    loop_edge = next(e for e in edges if e.condition == "loop")
    exit_edge = next(e for e in edges if e.condition == "exit")

    assert loop_edge.target == "A"
    assert exit_edge.target == "C"
    assert graph.has_cycles_with_exit()