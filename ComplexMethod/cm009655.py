def test_merge_tool_calls_parallel_same_index() -> None:
    """Test parallel tool calls with same index but different IDs."""
    # Two parallel tool calls with the same index but different IDs
    left = create_tool_call_chunk(
        name="read_file", args='{"path": "foo.txt"}', id="tooluse_ABC", index=0
    )
    right = create_tool_call_chunk(
        name="search_text", args='{"query": "bar"}', id="tooluse_DEF", index=0
    )
    merged = merge_lists([left], [right])
    assert merged is not None
    assert len(merged) == 2
    assert merged[0]["name"] == "read_file"
    assert merged[0]["id"] == "tooluse_ABC"
    assert merged[1]["name"] == "search_text"
    assert merged[1]["id"] == "tooluse_DEF"

    # Streaming continuation: same index, id=None on continuation chunk
    # should still merge correctly with the original chunk
    first = create_tool_call_chunk(name="tool1", args="", id="id1", index=0)
    continuation = create_tool_call_chunk(
        name=None, args='{"key": "value"}', id=None, index=0
    )
    merged = merge_lists([first], [continuation])
    assert merged is not None
    assert len(merged) == 1
    assert merged[0]["name"] == "tool1"
    assert merged[0]["args"] == '{"key": "value"}'
    assert merged[0]["id"] == "id1"

    # Three parallel tool calls all with the same index
    tc1 = create_tool_call_chunk(name="tool_a", args="{}", id="id_a", index=0)
    tc2 = create_tool_call_chunk(name="tool_b", args="{}", id="id_b", index=0)
    tc3 = create_tool_call_chunk(name="tool_c", args="{}", id="id_c", index=0)
    merged = merge_lists([tc1], [tc2], [tc3])
    assert merged is not None
    assert len(merged) == 3
    assert [m["name"] for m in merged] == ["tool_a", "tool_b", "tool_c"]
    assert [m["id"] for m in merged] == ["id_a", "id_b", "id_c"]