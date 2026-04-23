def test_vector_store_rag_dump(ingestion_graph, rag_graph):
    # Test ingestion graph dump
    ingestion_graph_dump = ingestion_graph.dump(
        name="Ingestion Graph", description="Graph for data ingestion", endpoint_name="ingestion"
    )
    assert isinstance(ingestion_graph_dump, dict)

    ingestion_data = ingestion_graph_dump["data"]
    assert "nodes" in ingestion_data
    assert "edges" in ingestion_data
    assert "description" in ingestion_graph_dump
    assert "endpoint_name" in ingestion_graph_dump

    ingestion_nodes = ingestion_data["nodes"]
    ingestion_edges = ingestion_data["edges"]
    assert len(ingestion_nodes) == 4  # There are 4 components in the ingestion graph
    assert len(ingestion_edges) == 3  # There are 3 connections between components

    # Test RAG graph dump
    rag_graph_dump = rag_graph.dump(
        name="RAG Graph", description="Graph for Retrieval-Augmented Generation", endpoint_name="rag"
    )
    assert isinstance(rag_graph_dump, dict)

    rag_data = rag_graph_dump["data"]
    assert "nodes" in rag_data
    assert "edges" in rag_data
    assert "description" in rag_graph_dump
    assert "endpoint_name" in rag_graph_dump

    rag_nodes = rag_data["nodes"]
    rag_edges = rag_data["edges"]
    assert len(rag_nodes) == 7  # There are 7 components in the RAG graph
    assert len(rag_edges) == 7