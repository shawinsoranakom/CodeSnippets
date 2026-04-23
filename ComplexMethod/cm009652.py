def test_complex_ai_message_chunks() -> None:
    assert AIMessageChunk(content=["I am"], id="ai4") + AIMessageChunk(
        content=[" indeed."]
    ) == AIMessageChunk(id="ai4", content=["I am", " indeed."]), (
        "Content concatenation with arrays of strings should naively combine"
    )

    assert AIMessageChunk(content=[{"index": 0, "text": "I am"}]) + AIMessageChunk(
        content=" indeed."
    ) == AIMessageChunk(content=[{"index": 0, "text": "I am"}, " indeed."]), (
        "Concatenating mixed content arrays should naively combine them"
    )

    assert AIMessageChunk(content=[{"index": 0, "text": "I am"}]) + AIMessageChunk(
        content=[{"index": 0, "text": " indeed."}]
    ) == AIMessageChunk(content=[{"index": 0, "text": "I am indeed."}]), (
        "Concatenating when both content arrays are dicts with the same index "
        "should merge"
    )

    assert AIMessageChunk(content=[{"index": 0, "text": "I am"}]) + AIMessageChunk(
        content=[{"text": " indeed."}]
    ) == AIMessageChunk(content=[{"index": 0, "text": "I am"}, {"text": " indeed."}]), (
        "Concatenating when one chunk is missing an index should not merge or throw"
    )

    assert AIMessageChunk(content=[{"index": 0, "text": "I am"}]) + AIMessageChunk(
        content=[{"index": 2, "text": " indeed."}]
    ) == AIMessageChunk(
        content=[{"index": 0, "text": "I am"}, {"index": 2, "text": " indeed."}]
    ), (
        "Concatenating when both content arrays are dicts with a gap between indexes "
        "should not result in a holey array"
    )

    assert AIMessageChunk(content=[{"index": 0, "text": "I am"}]) + AIMessageChunk(
        content=[{"index": 1, "text": " indeed."}]
    ) == AIMessageChunk(
        content=[{"index": 0, "text": "I am"}, {"index": 1, "text": " indeed."}]
    ), (
        "Concatenating when both content arrays are dicts with separate indexes "
        "should not merge"
    )

    assert AIMessageChunk(
        content=[{"index": 0, "text": "I am", "type": "text_block"}]
    ) + AIMessageChunk(
        content=[{"index": 0, "text": " indeed.", "type": "text_block"}]
    ) == AIMessageChunk(
        content=[{"index": 0, "text": "I am indeed.", "type": "text_block"}]
    ), (
        "Concatenating when both content arrays are dicts with the same index and type "
        "should merge"
    )

    assert AIMessageChunk(
        content=[{"index": 0, "text": "I am", "type": "text_block"}]
    ) + AIMessageChunk(
        content=[{"index": 0, "text": " indeed.", "type": "text_block_delta"}]
    ) == AIMessageChunk(
        content=[{"index": 0, "text": "I am indeed.", "type": "text_block"}]
    ), (
        "Concatenating when both content arrays are dicts with the same index "
        "and different types should merge without updating type"
    )

    assert AIMessageChunk(
        content=[{"index": 0, "text": "I am", "type": "text_block"}]
    ) + AIMessageChunk(
        content="", response_metadata={"extra": "value"}
    ) == AIMessageChunk(
        content=[{"index": 0, "text": "I am", "type": "text_block"}],
        response_metadata={"extra": "value"},
    ), (
        "Concatenating when one content is an array and one is an empty string "
        "should not add a new item, but should concat other fields"
    )