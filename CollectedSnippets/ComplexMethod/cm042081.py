def test_qdrant_store():
    qdrant_connection = QdrantConnection(memory=True)
    vectors_config = VectorParams(size=2, distance=Distance.COSINE)
    qdrant_store = QdrantStore(qdrant_connection)
    qdrant_store.create_collection("Book", vectors_config, force_recreate=True)
    assert qdrant_store.has_collection("Book") is True
    qdrant_store.delete_collection("Book")
    assert qdrant_store.has_collection("Book") is False
    qdrant_store.create_collection("Book", vectors_config)
    assert qdrant_store.has_collection("Book") is True
    qdrant_store.add("Book", points)
    results = qdrant_store.search("Book", query=[1.0, 1.0])
    assert results[0]["id"] == 2
    assert_almost_equal(results[0]["score"], 0.999106722578389)
    assert results[1]["id"] == 7
    assert_almost_equal(results[1]["score"], 0.9961650411397226)
    results = qdrant_store.search("Book", query=[1.0, 1.0], return_vector=True)
    assert results[0]["id"] == 2
    assert_almost_equal(results[0]["score"], 0.999106722578389)
    assert_almost_equal(results[0]["vector"], [0.7363563179969788, 0.6765939593315125])
    assert results[1]["id"] == 7
    assert_almost_equal(results[1]["score"], 0.9961650411397226)
    assert_almost_equal(results[1]["vector"], [0.7662628889083862, 0.6425272226333618])
    results = qdrant_store.search(
        "Book",
        query=[1.0, 1.0],
        query_filter=Filter(must=[FieldCondition(key="rand_number", range=Range(gte=8))]),
    )
    assert results[0]["id"] == 8
    assert_almost_equal(results[0]["score"], 0.9100373450784073)
    assert results[1]["id"] == 9
    assert_almost_equal(results[1]["score"], 0.7127610621127889)
    results = qdrant_store.search(
        "Book",
        query=[1.0, 1.0],
        query_filter=Filter(must=[FieldCondition(key="rand_number", range=Range(gte=8))]),
        return_vector=True,
    )
    assert_almost_equal(results[0]["vector"], [0.35037919878959656, 0.9366079568862915])
    assert_almost_equal(results[1]["vector"], [0.9999677538871765, 0.00802854634821415])