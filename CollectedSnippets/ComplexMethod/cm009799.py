def test_convert_to_v1_from_converse_chunk() -> None:
    chunks = [
        AIMessageChunk(
            content=[{"text": "Looking ", "type": "text", "index": 0}],
            response_metadata={"model_provider": "bedrock_converse"},
        ),
        AIMessageChunk(
            content=[{"text": "now.", "type": "text", "index": 0}],
            response_metadata={"model_provider": "bedrock_converse"},
        ),
        AIMessageChunk(
            content=[
                {
                    "type": "tool_use",
                    "name": "get_weather",
                    "input": {},
                    "id": "toolu_abc123",
                    "index": 1,
                }
            ],
            tool_call_chunks=[
                {
                    "type": "tool_call_chunk",
                    "name": "get_weather",
                    "args": "",
                    "id": "toolu_abc123",
                    "index": 1,
                }
            ],
            response_metadata={"model_provider": "bedrock_converse"},
        ),
        AIMessageChunk(
            content=[{"type": "input_json_delta", "partial_json": "", "index": 1}],
            tool_call_chunks=[
                {
                    "name": None,
                    "args": "",
                    "id": None,
                    "index": 1,
                    "type": "tool_call_chunk",
                }
            ],
            response_metadata={"model_provider": "bedrock_converse"},
        ),
        AIMessageChunk(
            content=[
                {"type": "input_json_delta", "partial_json": '{"loca', "index": 1}
            ],
            tool_call_chunks=[
                {
                    "name": None,
                    "args": '{"loca',
                    "id": None,
                    "index": 1,
                    "type": "tool_call_chunk",
                }
            ],
            response_metadata={"model_provider": "bedrock_converse"},
        ),
        AIMessageChunk(
            content=[
                {"type": "input_json_delta", "partial_json": 'tion": "San ', "index": 1}
            ],
            tool_call_chunks=[
                {
                    "name": None,
                    "args": 'tion": "San ',
                    "id": None,
                    "index": 1,
                    "type": "tool_call_chunk",
                }
            ],
            response_metadata={"model_provider": "bedrock_converse"},
        ),
        AIMessageChunk(
            content=[
                {"type": "input_json_delta", "partial_json": 'Francisco"}', "index": 1}
            ],
            tool_call_chunks=[
                {
                    "name": None,
                    "args": 'Francisco"}',
                    "id": None,
                    "index": 1,
                    "type": "tool_call_chunk",
                }
            ],
            response_metadata={"model_provider": "bedrock_converse"},
        ),
    ]
    expected_contents: list[types.ContentBlock] = [
        {"type": "text", "text": "Looking ", "index": 0},
        {"type": "text", "text": "now.", "index": 0},
        {
            "type": "tool_call_chunk",
            "name": "get_weather",
            "args": "",
            "id": "toolu_abc123",
            "index": 1,
        },
        {"name": None, "args": "", "id": None, "index": 1, "type": "tool_call_chunk"},
        {
            "name": None,
            "args": '{"loca',
            "id": None,
            "index": 1,
            "type": "tool_call_chunk",
        },
        {
            "name": None,
            "args": 'tion": "San ',
            "id": None,
            "index": 1,
            "type": "tool_call_chunk",
        },
        {
            "name": None,
            "args": 'Francisco"}',
            "id": None,
            "index": 1,
            "type": "tool_call_chunk",
        },
    ]
    for chunk, expected in zip(chunks, expected_contents, strict=False):
        assert chunk.content_blocks == [expected]

    full: AIMessageChunk | None = None
    for chunk in chunks:
        full = chunk if full is None else full + chunk
    assert isinstance(full, AIMessageChunk)

    expected_content = [
        {"type": "text", "text": "Looking now.", "index": 0},
        {
            "type": "tool_use",
            "name": "get_weather",
            "partial_json": '{"location": "San Francisco"}',
            "input": {},
            "id": "toolu_abc123",
            "index": 1,
        },
    ]
    assert full.content == expected_content

    expected_content_blocks = [
        {"type": "text", "text": "Looking now.", "index": 0},
        {
            "type": "tool_call_chunk",
            "name": "get_weather",
            "args": '{"location": "San Francisco"}',
            "id": "toolu_abc123",
            "index": 1,
        },
    ]
    assert full.content_blocks == expected_content_blocks