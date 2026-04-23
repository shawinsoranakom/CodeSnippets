async def test_output_version_astream(monkeypatch: Any) -> None:
    messages = [AIMessage("foo bar")]

    # v0
    llm = GenericFakeChatModel(messages=iter(messages))
    full = None
    async for chunk in llm.astream("hello"):
        assert isinstance(chunk, AIMessageChunk)
        assert isinstance(chunk.content, str)
        assert chunk.content
        full = chunk if full is None else full + chunk
    assert isinstance(full, AIMessageChunk)
    assert full.content == "foo bar"

    # v1
    llm = GenericFakeChatModel(messages=iter(messages), output_version="v1")
    full_v1: AIMessageChunk | None = None
    async for chunk in llm.astream("hello"):
        assert isinstance(chunk, AIMessageChunk)
        assert isinstance(chunk.content, list)
        assert len(chunk.content) == 1
        block = chunk.content[0]
        assert isinstance(block, dict)
        assert block["type"] == "text"
        assert block["text"]
        full_v1 = chunk if full_v1 is None else full_v1 + chunk
    assert isinstance(full_v1, AIMessageChunk)
    assert full_v1.response_metadata["output_version"] == "v1"

    assert full_v1.content == [{"type": "text", "text": "foo bar", "index": 0}]

    # Test text blocks
    llm_with_rich_content = _AnotherFakeChatModel(
        responses=iter([]),
        chunks=iter(
            [
                AIMessageChunk(content="foo "),
                AIMessageChunk(content="bar"),
            ]
        ),
        output_version="v1",
    )
    full_v1 = None
    async for chunk in llm_with_rich_content.astream("hello"):
        full_v1 = chunk if full_v1 is None else full_v1 + chunk
    assert isinstance(full_v1, AIMessageChunk)
    assert full_v1.content_blocks == [{"type": "text", "text": "foo bar", "index": 0}]

    # Test content blocks of different types
    chunks = [
        AIMessageChunk(content="", additional_kwargs={"reasoning_content": "<rea"}),
        AIMessageChunk(content="", additional_kwargs={"reasoning_content": "soning>"}),
        AIMessageChunk(content="<some "),
        AIMessageChunk(content="text>"),
    ]
    llm_with_rich_content = _AnotherFakeChatModel(
        responses=iter([]),
        chunks=iter(chunks),
        output_version="v1",
    )
    full_v1 = None
    async for chunk in llm_with_rich_content.astream("hello"):
        full_v1 = chunk if full_v1 is None else full_v1 + chunk
    assert isinstance(full_v1, AIMessageChunk)
    assert full_v1.content_blocks == [
        {"type": "reasoning", "reasoning": "<reasoning>", "index": 0},
        {"type": "text", "text": "<some text>", "index": 1},
    ]

    # Test invoke with stream=True
    llm_with_rich_content = _AnotherFakeChatModel(
        responses=iter([]),
        chunks=iter(chunks),
        output_version="v1",
    )
    response_v1 = await llm_with_rich_content.ainvoke("hello", stream=True)
    assert response_v1.content_blocks == [
        {"type": "reasoning", "reasoning": "<reasoning>", "index": 0},
        {"type": "text", "text": "<some text>", "index": 1},
    ]

    # v1 from env var
    monkeypatch.setenv("LC_OUTPUT_VERSION", "v1")
    llm = GenericFakeChatModel(messages=iter(messages))
    full_env = None
    async for chunk in llm.astream("hello"):
        assert isinstance(chunk, AIMessageChunk)
        assert isinstance(chunk.content, list)
        assert len(chunk.content) == 1
        block = chunk.content[0]
        assert isinstance(block, dict)
        assert block["type"] == "text"
        assert block["text"]
        full_env = chunk if full_env is None else full_env + chunk
    assert isinstance(full_env, AIMessageChunk)
    assert full_env.response_metadata["output_version"] == "v1"
    assert messages == _normalize_messages(messages)