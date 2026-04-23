def test_sentence_transformer_embedder_with_common_parameter():
    table = pw.debug.table_from_rows(
        schema=pw.schema_from_types(text=str), rows=[("aaa",), ("bbb",)]
    )

    embedder = embedders.SentenceTransformerEmbedder(model="intfloat/e5-large-v2")

    table = table.select(embedding=embedder(pw.this.text, normalize_embeddings=True))

    result = pw.debug.table_to_pandas(table).to_dict("records")

    assert len(result) == 2
    assert isinstance(result[0]["embedding"][0], float)
    assert len(result[0]["embedding"]) == 1024
    assert abs(sum([x * x for x in result[0]["embedding"]]) - 1.0) < 0.001
    assert isinstance(result[1]["embedding"][0], float)
    assert len(result[1]["embedding"]) == 1024
    assert abs(sum([x * x for x in result[1]["embedding"]]) - 1.0) < 0.001