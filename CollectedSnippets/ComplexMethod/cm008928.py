def test_split_json_empty_dict_value_in_large_payload() -> None:
    """Test that empty dict values survive chunking in a larger payload."""
    max_chunk = 200
    splitter = RecursiveJsonSplitter(max_chunk_size=max_chunk)

    data: dict[str, Any] = {
        "key0": "x" * 50,
        "empty": {},
        "key1": "y" * 50,
        "nested": {f"k{i}": f"v{i}" for i in range(20)},
    }
    chunks = splitter.split_json(data)

    # Verify all chunks are within size limits
    for chunk in chunks:
        assert len(json.dumps(chunk)) < max_chunk * 1.05

    # Verify the empty dict is somewhere in the chunks
    found_empty = False
    for chunk in chunks:
        # Walk nested structure to find "empty": {}
        if "empty" in chunk and chunk["empty"] == {}:
            found_empty = True
            break
        for v in chunk.values():
            if isinstance(v, dict) and "empty" in v and v["empty"] == {}:
                found_empty = True
                break
    assert found_empty, "Empty dict value was lost during splitting"