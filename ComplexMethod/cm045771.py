def test_openai_embedder_with_different_parameter():
    table = pw.debug.table_from_rows(
        schema=pw.schema_from_types(text=str, dimensions=int),
        rows=[("aaa", 300), ("bbb", 800)],
    )

    embedder = embedders.OpenAIEmbedder(
        model="text-embedding-3-small",
        retry_strategy=pw.udfs.ExponentialBackoffRetryStrategy(),
    )

    table = table.select(
        text=pw.this.text,
        embedding=embedder(pw.this.text, dimensions=pw.this.dimensions),
    )

    result = pw.debug.table_to_pandas(table).to_dict("records")

    assert len(result) == 2
    assert isinstance(result[0]["embedding"][0], float)
    assert isinstance(result[1]["embedding"][0], float)
    if result[0]["text"] == "aaa":
        assert len(result[0]["embedding"]) == 300
    else:
        assert len(result[1]["embedding"]) == 300
    if result[0]["text"] == "bbb":
        assert len(result[0]["embedding"]) == 800
    else:
        assert len(result[1]["embedding"]) == 800