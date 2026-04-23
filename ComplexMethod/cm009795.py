def test_content_blocks() -> None:
    message = AIMessage(
        "",
        tool_calls=[
            {"type": "tool_call", "name": "foo", "args": {"a": "b"}, "id": "abc_123"}
        ],
    )
    assert len(message.content_blocks) == 1
    assert message.content_blocks[0]["type"] == "tool_call"
    assert message.content_blocks == [
        {"type": "tool_call", "id": "abc_123", "name": "foo", "args": {"a": "b"}}
    ]
    assert message.content == ""

    message = AIMessage(
        "foo",
        tool_calls=[
            {"type": "tool_call", "name": "foo", "args": {"a": "b"}, "id": "abc_123"}
        ],
    )
    assert len(message.content_blocks) == 2
    assert message.content_blocks[0]["type"] == "text"
    assert message.content_blocks[1]["type"] == "tool_call"
    assert message.content_blocks == [
        {"type": "text", "text": "foo"},
        {"type": "tool_call", "id": "abc_123", "name": "foo", "args": {"a": "b"}},
    ]
    assert message.content == "foo"

    # With standard blocks
    standard_content: list[types.ContentBlock] = [
        {"type": "reasoning", "reasoning": "foo"},
        {"type": "text", "text": "bar"},
        {
            "type": "text",
            "text": "baz",
            "annotations": [{"type": "citation", "url": "http://example.com"}],
        },
        {
            "type": "image",
            "url": "http://example.com/image.png",
            "extras": {"foo": "bar"},
        },
        {
            "type": "non_standard",
            "value": {"custom_key": "custom_value", "another_key": 123},
        },
        {
            "type": "tool_call",
            "name": "foo",
            "args": {"a": "b"},
            "id": "abc_123",
        },
    ]
    missing_tool_call: types.ToolCall = {
        "type": "tool_call",
        "name": "bar",
        "args": {"c": "d"},
        "id": "abc_234",
    }
    message = AIMessage(
        content_blocks=standard_content,
        tool_calls=[
            {"type": "tool_call", "name": "foo", "args": {"a": "b"}, "id": "abc_123"},
            missing_tool_call,
        ],
    )
    assert message.content_blocks == [*standard_content, missing_tool_call]

    # Check we auto-populate tool_calls
    standard_content = [
        {"type": "text", "text": "foo"},
        {
            "type": "tool_call",
            "name": "foo",
            "args": {"a": "b"},
            "id": "abc_123",
        },
        missing_tool_call,
    ]
    message = AIMessage(content_blocks=standard_content)
    assert message.tool_calls == [
        {"type": "tool_call", "name": "foo", "args": {"a": "b"}, "id": "abc_123"},
        missing_tool_call,
    ]

    # Chunks
    message = AIMessageChunk(
        content="",
        tool_call_chunks=[
            {
                "type": "tool_call_chunk",
                "name": "foo",
                "args": "",
                "id": "abc_123",
                "index": 0,
            }
        ],
    )
    assert len(message.content_blocks) == 1
    assert message.content_blocks[0]["type"] == "tool_call_chunk"
    assert message.content_blocks == [
        {
            "type": "tool_call_chunk",
            "name": "foo",
            "args": "",
            "id": "abc_123",
            "index": 0,
        }
    ]
    assert message.content == ""

    # Test we parse tool call chunks into tool calls for v1 content
    chunk_1 = AIMessageChunk(
        content="",
        tool_call_chunks=[
            {
                "type": "tool_call_chunk",
                "name": "foo",
                "args": '{"foo": "b',
                "id": "abc_123",
                "index": 0,
            }
        ],
    )

    chunk_2 = AIMessageChunk(
        content="",
        tool_call_chunks=[
            {
                "type": "tool_call_chunk",
                "name": "",
                "args": 'ar"}',
                "id": "abc_123",
                "index": 0,
            }
        ],
    )
    chunk_3 = AIMessageChunk(content="", chunk_position="last")
    chunk = chunk_1 + chunk_2 + chunk_3
    assert chunk.content == ""
    assert chunk.content_blocks == chunk.tool_calls

    # test v1 content
    chunk_1.content = cast("str | list[str | dict]", chunk_1.content_blocks)
    assert len(chunk_1.content) == 1
    chunk_1.content[0]["extras"] = {"baz": "qux"}  # type: ignore[index]
    chunk_1.response_metadata["output_version"] = "v1"
    chunk_2.content = cast("str | list[str | dict]", chunk_2.content_blocks)

    chunk = chunk_1 + chunk_2 + chunk_3
    assert chunk.content == [
        {
            "type": "tool_call",
            "name": "foo",
            "args": {"foo": "bar"},
            "id": "abc_123",
            "extras": {"baz": "qux"},
        }
    ]

    # Non-standard
    standard_content_1: list[types.ContentBlock] = [
        {"type": "non_standard", "index": 0, "value": {"foo": "bar "}}
    ]
    standard_content_2: list[types.ContentBlock] = [
        {"type": "non_standard", "index": 0, "value": {"foo": "baz"}}
    ]
    chunk_1 = AIMessageChunk(content=cast("str | list[str | dict]", standard_content_1))
    chunk_2 = AIMessageChunk(content=cast("str | list[str | dict]", standard_content_2))
    merged_chunk = chunk_1 + chunk_2
    assert merged_chunk.content == [
        {"type": "non_standard", "index": 0, "value": {"foo": "bar baz"}},
    ]

    # Test server_tool_call_chunks
    chunk_1 = AIMessageChunk(
        content=[
            {
                "type": "server_tool_call_chunk",
                "index": 0,
                "name": "foo",
            }
        ]
    )
    chunk_2 = AIMessageChunk(
        content=[{"type": "server_tool_call_chunk", "index": 0, "args": '{"a'}]
    )
    chunk_3 = AIMessageChunk(
        content=[{"type": "server_tool_call_chunk", "index": 0, "args": '": 1}'}]
    )
    merged_chunk = chunk_1 + chunk_2 + chunk_3
    assert merged_chunk.content == [
        {
            "type": "server_tool_call_chunk",
            "name": "foo",
            "index": 0,
            "args": '{"a": 1}',
        }
    ]

    full_chunk = merged_chunk + AIMessageChunk(
        content=[], chunk_position="last", response_metadata={"output_version": "v1"}
    )
    assert full_chunk.content == [
        {"type": "server_tool_call", "name": "foo", "index": 0, "args": {"a": 1}}
    ]

    # Test non-standard + non-standard
    chunk_1 = AIMessageChunk(
        content=[
            {
                "type": "non_standard",
                "index": 0,
                "value": {"type": "non_standard_tool", "foo": "bar"},
            }
        ]
    )
    chunk_2 = AIMessageChunk(
        content=[
            {
                "type": "non_standard",
                "index": 0,
                "value": {"type": "input_json_delta", "partial_json": "a"},
            }
        ]
    )
    chunk_3 = AIMessageChunk(
        content=[
            {
                "type": "non_standard",
                "index": 0,
                "value": {"type": "input_json_delta", "partial_json": "b"},
            }
        ]
    )
    merged_chunk = chunk_1 + chunk_2 + chunk_3
    assert merged_chunk.content == [
        {
            "type": "non_standard",
            "index": 0,
            "value": {"type": "non_standard_tool", "foo": "bar", "partial_json": "ab"},
        }
    ]

    # Test standard + non-standard with same index
    standard_content_1 = [
        {
            "type": "server_tool_call",
            "name": "web_search",
            "id": "ws_123",
            "args": {"query": "web query"},
            "index": 0,
        }
    ]
    standard_content_2 = [{"type": "non_standard", "value": {"foo": "bar"}, "index": 0}]
    chunk_1 = AIMessageChunk(content=cast("str | list[str | dict]", standard_content_1))
    chunk_2 = AIMessageChunk(content=cast("str | list[str | dict]", standard_content_2))
    merged_chunk = chunk_1 + chunk_2
    assert merged_chunk.content == [
        {
            "type": "server_tool_call",
            "name": "web_search",
            "id": "ws_123",
            "args": {"query": "web query"},
            "index": 0,
            "extras": {"foo": "bar"},
        }
    ]