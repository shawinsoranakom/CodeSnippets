def test_process_flow_vector_store_grouped(vector_store_grouped_json_flow):
    grouped_chat_data = json.loads(vector_store_grouped_json_flow).get("data")
    nodes = grouped_chat_data["nodes"]
    assert len(nodes) == 4
    # There are two group nodes in this flow
    # One of them is inside the other totalling 7 nodes
    # 4 nodes grouped, one of these turns into 1 normal node and 1 group node
    # This group node has 2 nodes inside it

    processed_flow = process_flow(grouped_chat_data)
    assert processed_flow is not None
    processed_nodes = processed_flow["nodes"]
    assert len(processed_nodes) == 7
    assert isinstance(processed_flow, dict)
    assert "nodes" in processed_flow
    assert "edges" in processed_flow
    edges = processed_flow["edges"]
    # Expected keywords in source and target fields
    expected_keywords = [
        {"source": "VectorStoreInfo", "target": "VectorStoreAgent"},
        {"source": "ChatOpenAI", "target": "VectorStoreAgent"},
        {"source": "OpenAIEmbeddings", "target": "Chroma"},
        {"source": "Chroma", "target": "VectorStoreInfo"},
        {"source": "WebBaseLoader", "target": "RecursiveCharacterTextSplitter"},
        {"source": "RecursiveCharacterTextSplitter", "target": "Chroma"},
    ]

    for idx, expected_keyword in enumerate(expected_keywords):
        for key, value in expected_keyword.items():
            assert value in edges[idx][key].split("-")[0], (
                f"Edge {idx}, key {key} expected to contain {value} but got {edges[idx][key]}"
            )