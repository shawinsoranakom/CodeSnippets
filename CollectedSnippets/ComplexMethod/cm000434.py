async def test_graph_creation(server: SpinTestServer, snapshot: Snapshot):
    """
    Test the creation of a graph with nodes and links.

    This test ensures that:
    1. A graph can be successfully created with valid connections.
    2. The created graph has the correct structure and properties.

    Args:
        server (SpinTestServer): The test server instance.
    """
    value_block = StoreValueBlock().id
    input_block = AgentInputBlock().id

    graph = Graph(
        id="test_graph",
        name="TestGraph",
        description="Test graph",
        nodes=[
            Node(id="node_1", block_id=value_block),
            Node(id="node_2", block_id=input_block, input_default={"name": "input"}),
            Node(id="node_3", block_id=value_block),
        ],
        links=[
            Link(
                source_id="node_1",
                sink_id="node_2",
                source_name="output",
                sink_name="name",
            ),
        ],
    )
    create_graph = CreateGraph(graph=graph)
    created_graph = await server.agent_server.test_create_graph(
        create_graph, DEFAULT_USER_ID
    )

    assert UUID(created_graph.id)
    assert created_graph.name == "TestGraph"

    assert len(created_graph.nodes) == 3
    assert UUID(created_graph.nodes[0].id)
    assert UUID(created_graph.nodes[1].id)
    assert UUID(created_graph.nodes[2].id)

    nodes = created_graph.nodes
    links = created_graph.links
    assert len(links) == 1
    assert links[0].source_id != links[0].sink_id
    assert links[0].source_id in {nodes[0].id, nodes[1].id, nodes[2].id}
    assert links[0].sink_id in {nodes[0].id, nodes[1].id, nodes[2].id}

    # Create a serializable version of the graph for snapshot testing
    # Remove dynamic IDs to make snapshots reproducible
    graph_data = {
        "name": created_graph.name,
        "description": created_graph.description,
        "nodes_count": len(created_graph.nodes),
        "links_count": len(created_graph.links),
        "node_blocks": [node.block_id for node in created_graph.nodes],
        "link_structure": [
            {"source_name": link.source_name, "sink_name": link.sink_name}
            for link in created_graph.links
        ],
    }
    snapshot.snapshot_dir = "snapshots"
    snapshot.assert_match(
        json.dumps(graph_data, indent=2, sort_keys=True), "grph_struct"
    )