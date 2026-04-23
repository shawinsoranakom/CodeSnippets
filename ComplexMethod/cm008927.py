def test_split_json_mixed_empty_and_nonempty_dicts() -> None:
    """Test a realistic structure mixing empty and non-empty nested dicts."""
    splitter = RecursiveJsonSplitter(max_chunk_size=300)

    data: dict[str, Any] = {
        "config": {},
        "metadata": {"author": "test", "tags": {}},
        "content": "some text",
    }
    chunks = splitter.split_json(data)
    merged: dict[str, Any] = {}
    for chunk in chunks:
        for k, v in chunk.items():
            if k in merged and isinstance(merged[k], dict) and isinstance(v, dict):
                merged[k].update(v)
            else:
                merged[k] = v

    assert merged["config"] == {}
    assert merged["metadata"] == {"author": "test", "tags": {}}
    assert merged["content"] == "some text"