def test_merge_tool_calls() -> None:
    tool_call_1 = create_tool_call_chunk(name="tool1", args="", id="1", index=0)
    tool_call_2 = create_tool_call_chunk(
        name=None, args='{"arg1": "val', id=None, index=0
    )
    tool_call_3 = create_tool_call_chunk(name=None, args='ue}"', id=None, index=0)
    merged = merge_lists([tool_call_1], [tool_call_2])
    assert merged is not None
    assert merged == [
        {
            "name": "tool1",
            "args": '{"arg1": "val',
            "id": "1",
            "index": 0,
            "type": "tool_call_chunk",
        }
    ]
    merged = merge_lists(merged, [tool_call_3])
    assert merged is not None
    assert merged == [
        {
            "name": "tool1",
            "args": '{"arg1": "value}"',
            "id": "1",
            "index": 0,
            "type": "tool_call_chunk",
        }
    ]

    left = create_tool_call_chunk(
        name="tool1", args='{"arg1": "value1"}', id="1", index=None
    )
    right = create_tool_call_chunk(
        name="tool2", args='{"arg2": "value2"}', id="1", index=None
    )
    merged = merge_lists([left], [right])
    assert merged is not None
    assert len(merged) == 2

    left = create_tool_call_chunk(
        name="tool1", args='{"arg1": "value1"}', id=None, index=None
    )
    right = create_tool_call_chunk(
        name="tool1", args='{"arg2": "value2"}', id=None, index=None
    )
    merged = merge_lists([left], [right])
    assert merged is not None
    assert len(merged) == 2

    left = create_tool_call_chunk(
        name="tool1", args='{"arg1": "value1"}', id="1", index=0
    )
    right = create_tool_call_chunk(
        name="tool2", args='{"arg2": "value2"}', id=None, index=1
    )
    merged = merge_lists([left], [right])
    assert merged is not None
    assert len(merged) == 2