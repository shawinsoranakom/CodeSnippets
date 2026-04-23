def test_memory_chatbot_dump_structure(memory_chatbot_graph: Graph):
    # Now we run step by step
    graph_dict = memory_chatbot_graph.dump(
        name="Memory Chatbot", description="A memory chatbot", endpoint_name="membot"
    )
    assert isinstance(graph_dict, dict)
    # Test structure
    assert "data" in graph_dict
    assert "is_component" in graph_dict

    data_dict = graph_dict["data"]
    assert "nodes" in data_dict
    assert "edges" in data_dict
    assert "description" in graph_dict
    assert "endpoint_name" in graph_dict

    # Test data
    nodes = data_dict["nodes"]
    edges = data_dict["edges"]
    description = graph_dict["description"]
    endpoint_name = graph_dict["endpoint_name"]

    assert len(nodes) == 6
    assert len(edges) == 5
    assert description is not None
    assert endpoint_name is not None