async def test_vector_store_rag(ingestion_graph, rag_graph):
    assert ingestion_graph is not None
    ingestion_ids = [
        "file-123",
        "text-splitter-123",
        "openai-embeddings-123",
        "ingestion-vector-store-123",
    ]
    assert rag_graph is not None
    rag_ids = [
        "chatinput-123",
        "chatoutput-123",
        "openai-123",
        "parse-data-123",
        "prompt-123",
        "rag-vector-store-123",
        "openai-embeddings-124",
    ]
    for ids, graph, len_results in [(ingestion_ids, ingestion_graph, 5), (rag_ids, rag_graph, 8)]:
        results = [result async for result in graph.async_start(reset_output_values=False)]
        assert len(results) == len_results
        vids = [result.vertex.id for result in results if hasattr(result, "vertex")]
        assert all(vid in ids for vid in vids), f"Diff: {set(vids) - set(ids)}"
        assert results[-1] == Finish()