def test_add_conditional_edges() -> None:
    client = ReplayChatCompletionClient(["1", "2"])
    a = AssistantAgent("A", model_client=client)
    b = AssistantAgent("B", model_client=client)
    c = AssistantAgent("C", model_client=client)

    builder = DiGraphBuilder()
    builder.add_node(a).add_node(b).add_node(c)
    builder.add_conditional_edges(a, {"yes": b, "no": c})

    edges = builder.nodes["A"].edges
    assert len(edges) == 2

    # Extract the condition strings to compare them
    conditions = [e.condition for e in edges]
    assert "yes" in conditions
    assert "no" in conditions

    # Match edge targets with conditions
    yes_edge = next(e for e in edges if e.condition == "yes")
    no_edge = next(e for e in edges if e.condition == "no")

    assert yes_edge.target == "B"
    assert no_edge.target == "C"