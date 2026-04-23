def test_response_structure(server: RemoteOpenAIServer, model_name: str):
    r = _cohere_embed(server, model_name, texts=["test"], embedding_types=["float"])
    assert "id" in r
    assert "embeddings" in r
    assert "texts" in r
    assert r["texts"] == ["test"]
    assert "meta" in r
    assert r["meta"]["api_version"]["version"] == "2"
    assert "billed_units" in r["meta"]
    assert r["meta"]["billed_units"]["input_tokens"] > 0
    assert r["meta"]["billed_units"]["image_tokens"] == 0