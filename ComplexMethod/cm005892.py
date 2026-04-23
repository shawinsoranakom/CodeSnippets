def test_vector_store_rag_dump_components_and_edges(ingestion_graph, rag_graph):
    # Test ingestion graph components and edges
    ingestion_graph_dump = ingestion_graph.dump(
        name="Ingestion Graph", description="Graph for data ingestion", endpoint_name="ingestion"
    )

    ingestion_data = ingestion_graph_dump["data"]
    ingestion_nodes = ingestion_data["nodes"]
    ingestion_edges = ingestion_data["edges"]

    # Define expected nodes with their types
    expected_nodes = {
        "file-123": "File",
        "openai-embeddings-123": "OpenAIEmbeddings",
        "text-splitter-123": "SplitText",
        "ingestion-vector-store-123": "AstraDB",
    }

    # Verify number of nodes
    assert len(ingestion_nodes) == len(expected_nodes), "Unexpected number of nodes"

    # Create a mapping of node IDs to their data for easier lookup
    node_map = {node["id"]: node["data"] for node in ingestion_nodes}

    # Verify each expected node exists with correct type
    for node_id, expected_type in expected_nodes.items():
        assert node_id in node_map, f"Missing node {node_id}"
        assert node_map[node_id]["type"] == expected_type, (
            f"Node {node_id} has incorrect type. Expected {expected_type}, got {node_map[node_id]['type']}"
        )

    # Verify all nodes in graph are expected
    unexpected_nodes = set(node_map.keys()) - set(expected_nodes.keys())
    assert not unexpected_nodes, f"Found unexpected nodes: {unexpected_nodes}"

    # Check edges in the ingestion graph
    expected_ingestion_edges = [
        ("file-123", "text-splitter-123"),
        ("text-splitter-123", "ingestion-vector-store-123"),
        ("openai-embeddings-123", "ingestion-vector-store-123"),
    ]
    assert len(ingestion_edges) == len(expected_ingestion_edges)

    for edge in ingestion_edges:
        source = edge["source"]
        target = edge["target"]
        assert (source, target) in expected_ingestion_edges, edge

    # Test RAG graph components and edges
    rag_graph_dump = rag_graph.dump(
        name="RAG Graph", description="Graph for Retrieval-Augmented Generation", endpoint_name="rag"
    )

    rag_data = rag_graph_dump["data"]
    rag_nodes = rag_data["nodes"]
    rag_edges = rag_data["edges"]

    # Sort nodes by id to check components
    rag_nodes = sorted(rag_nodes, key=operator.itemgetter("id"))

    # Check components in the RAG graph
    assert rag_nodes[0]["data"]["type"] == "ChatInput"
    assert rag_nodes[0]["id"] == "chatinput-123"

    assert rag_nodes[1]["data"]["type"] == "ChatOutput"
    assert rag_nodes[1]["id"] == "chatoutput-123"

    assert rag_nodes[2]["data"]["type"] == "OpenAIModel"
    assert rag_nodes[2]["id"] == "openai-123"

    assert rag_nodes[3]["data"]["type"] == "OpenAIEmbeddings"
    assert rag_nodes[3]["id"] == "openai-embeddings-124"

    assert rag_nodes[4]["data"]["type"] == "ParseData"
    assert rag_nodes[4]["id"] == "parse-data-123"

    assert rag_nodes[5]["data"]["type"] == "Prompt Template"
    assert rag_nodes[5]["id"] == "prompt-123"

    assert rag_nodes[6]["data"]["type"] == "AstraDB"
    assert rag_nodes[6]["id"] == "rag-vector-store-123"

    # Check edges in the RAG graph
    expected_rag_edges = [
        ("chatinput-123", "rag-vector-store-123"),
        ("openai-embeddings-124", "rag-vector-store-123"),
        ("chatinput-123", "prompt-123"),
        ("rag-vector-store-123", "parse-data-123"),
        ("parse-data-123", "prompt-123"),
        ("prompt-123", "openai-123"),
        ("openai-123", "chatoutput-123"),
    ]
    assert len(rag_edges) == len(expected_rag_edges), rag_edges

    for edge in rag_edges:
        source = edge["source"]
        target = edge["target"]
        assert (source, target) in expected_rag_edges, f"Edge {source} -> {target} not found"