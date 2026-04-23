def test_memory_chatbot_dump_components_and_edges(memory_chatbot_graph: Graph):
    # Check all components and edges were dumped correctly
    graph_dict: GraphDump = memory_chatbot_graph.dump(
        name="Memory Chatbot", description="A memory chatbot", endpoint_name="membot"
    )

    data_dict = graph_dict["data"]
    nodes = data_dict["nodes"]
    edges = data_dict["edges"]

    # sort the nodes by id
    nodes = sorted(nodes, key=operator.itemgetter("id"))

    # Check each node
    assert nodes[0]["data"]["type"] == "ChatInput"
    assert nodes[0]["id"] == "chat_input"

    assert nodes[1]["data"]["type"] == "Memory"
    assert nodes[1]["id"] == "chat_memory"

    assert nodes[2]["data"]["type"] == "ChatOutput"
    assert nodes[2]["id"] == "chat_output"

    assert nodes[3]["data"]["type"] == "OpenAIModel"
    assert nodes[3]["id"] == "openai"

    assert nodes[4]["data"]["type"] == "Prompt Template"
    assert nodes[4]["id"] == "prompt"

    # Check edges
    expected_edges = [
        ("chat_input", "prompt"),
        ("chat_memory", "type_converter"),
        ("type_converter", "prompt"),
        ("prompt", "openai"),
        ("openai", "chat_output"),
    ]

    assert len(edges) == len(expected_edges)

    for edge in edges:
        source = edge["source"]
        target = edge["target"]
        assert (source, target) in expected_edges, edge