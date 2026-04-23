def test_vector_store_rag_add(ingestion_graph: Graph, rag_graph: Graph):
    ingestion_graph_copy = copy.deepcopy(ingestion_graph)
    rag_graph_copy = copy.deepcopy(rag_graph)
    ingestion_graph_copy += rag_graph_copy

    assert len(ingestion_graph_copy.vertices) == len(ingestion_graph.vertices) + len(rag_graph.vertices), (
        f"Vertices mismatch: {len(ingestion_graph_copy.vertices)} "
        f"!= {len(ingestion_graph.vertices)} + {len(rag_graph.vertices)}"
    )
    assert len(ingestion_graph_copy.edges) == len(ingestion_graph.edges) + len(rag_graph.edges), (
        f"Edges mismatch: {len(ingestion_graph_copy.edges)} != {len(ingestion_graph.edges)} + {len(rag_graph.edges)}"
    )

    combined_graph_dump = ingestion_graph_copy.dump(
        name="Combined Graph", description="Graph for data ingestion and RAG", endpoint_name="combined"
    )

    combined_data = combined_graph_dump["data"]
    combined_nodes = combined_data["nodes"]
    combined_edges = combined_data["edges"]

    # Sort nodes by id to check components
    combined_nodes = sorted(combined_nodes, key=operator.itemgetter("id"))

    # Expected components in the combined graph (both ingestion and RAG nodes)
    expected_nodes = sorted(
        [
            {"id": "file-123", "type": "File"},
            {"id": "openai-embeddings-123", "type": "OpenAIEmbeddings"},
            {"id": "text-splitter-123", "type": "SplitText"},
            {"id": "ingestion-vector-store-123", "type": "AstraDB"},
            {"id": "chatinput-123", "type": "ChatInput"},
            {"id": "chatoutput-123", "type": "ChatOutput"},
            {"id": "openai-123", "type": "OpenAIModel"},
            {"id": "openai-embeddings-124", "type": "OpenAIEmbeddings"},
            {"id": "parse-data-123", "type": "ParseData"},
            {"id": "prompt-123", "type": "Prompt Template"},
            {"id": "rag-vector-store-123", "type": "AstraDB"},
        ],
        key=operator.itemgetter("id"),
    )

    for expected_node, combined_node in zip(expected_nodes, combined_nodes, strict=True):
        assert combined_node["data"]["type"] == expected_node["type"]
        assert combined_node["id"] == expected_node["id"]

    # Expected edges in the combined graph (both ingestion and RAG edges)
    expected_combined_edges = [
        ("file-123", "text-splitter-123"),
        ("text-splitter-123", "ingestion-vector-store-123"),
        ("openai-embeddings-123", "ingestion-vector-store-123"),
        ("chatinput-123", "rag-vector-store-123"),
        ("openai-embeddings-124", "rag-vector-store-123"),
        ("chatinput-123", "prompt-123"),
        ("rag-vector-store-123", "parse-data-123"),
        ("parse-data-123", "prompt-123"),
        ("prompt-123", "openai-123"),
        ("openai-123", "chatoutput-123"),
    ]

    assert len(combined_edges) == len(expected_combined_edges), combined_edges

    for edge in combined_edges:
        source = edge["source"]
        target = edge["target"]
        assert (source, target) in expected_combined_edges, f"Edge {source} -> {target} not found"