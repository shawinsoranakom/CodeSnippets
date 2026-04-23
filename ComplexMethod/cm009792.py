def test_graph_single_runnable(snapshot: SnapshotAssertion) -> None:
    runnable = StrOutputParser()
    graph = StrOutputParser().get_graph()
    first_node = graph.first_node()
    assert first_node is not None
    assert first_node.data.model_json_schema() == runnable.get_input_jsonschema()  # type: ignore[union-attr]
    last_node = graph.last_node()
    assert last_node is not None
    assert last_node.data.model_json_schema() == runnable.get_output_jsonschema()  # type: ignore[union-attr]
    assert len(graph.nodes) == 3
    assert len(graph.edges) == 2
    assert graph.edges[0].source == first_node.id
    assert graph.edges[1].target == last_node.id
    assert graph.draw_ascii() == snapshot(name="ascii")
    assert graph.draw_mermaid() == snapshot(name="mermaid")

    graph.trim_first_node()
    first_node = graph.first_node()
    assert first_node is not None
    assert first_node.data == runnable

    graph.trim_last_node()
    last_node = graph.last_node()
    assert last_node is not None
    assert last_node.data == runnable