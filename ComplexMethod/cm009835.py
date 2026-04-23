async def test_generic_fake_chat_model_stream() -> None:
    """Test streaming."""
    infinite_cycle = cycle(
        [
            AIMessage(content="hello goodbye"),
        ],
    )
    model = GenericFakeChatModel(messages=infinite_cycle)
    chunks = [chunk async for chunk in model.astream("meow")]
    assert chunks == [
        _AnyIdAIMessageChunk(content="hello"),
        _AnyIdAIMessageChunk(content=" "),
        _AnyIdAIMessageChunk(content="goodbye", chunk_position="last"),
    ]

    chunks = list(model.stream("meow"))
    assert chunks == [
        _AnyIdAIMessageChunk(content="hello"),
        _AnyIdAIMessageChunk(content=" "),
        _AnyIdAIMessageChunk(content="goodbye", chunk_position="last"),
    ]

    # Test streaming of additional kwargs.
    # Relying on insertion order of the additional kwargs dict
    message = AIMessage(content="", additional_kwargs={"foo": 42, "bar": 24})
    model = GenericFakeChatModel(messages=cycle([message]))
    chunks = [chunk async for chunk in model.astream("meow")]
    assert chunks == [
        _AnyIdAIMessageChunk(content="", additional_kwargs={"foo": 42}),
        _AnyIdAIMessageChunk(content="", additional_kwargs={"bar": 24}),
        _AnyIdAIMessageChunk(content="", chunk_position="last"),
    ]

    message = AIMessage(
        id="a1",
        content="",
        additional_kwargs={
            "function_call": {
                "name": "move_file",
                "arguments": '{\n  "source_path": "foo",\n  "'
                'destination_path": "bar"\n}',
            },
        },
    )
    model = GenericFakeChatModel(messages=cycle([message]))
    chunks = [chunk async for chunk in model.astream("meow")]

    assert chunks == [
        AIMessageChunk(
            content="",
            additional_kwargs={"function_call": {"name": "move_file"}},
            id="a1",
        ),
        AIMessageChunk(
            id="a1",
            content="",
            additional_kwargs={
                "function_call": {"arguments": '{\n  "source_path": "foo"'},
            },
        ),
        AIMessageChunk(
            id="a1",
            content="",
            additional_kwargs={"function_call": {"arguments": ","}},
        ),
        AIMessageChunk(
            id="a1",
            content="",
            additional_kwargs={
                "function_call": {"arguments": '\n  "destination_path": "bar"\n}'},
            },
        ),
        _AnyIdAIMessageChunk(content="", chunk_position="last"),
    ]

    accumulate_chunks = None
    for chunk in chunks:
        if accumulate_chunks is None:
            accumulate_chunks = chunk
        else:
            accumulate_chunks += chunk

    assert accumulate_chunks == AIMessageChunk(
        id="a1",
        content="",
        additional_kwargs={
            "function_call": {
                "name": "move_file",
                "arguments": '{\n  "source_path": "foo",\n  "'
                'destination_path": "bar"\n}',
            },
        },
        chunk_position="last",
    )