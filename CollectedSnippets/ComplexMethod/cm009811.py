async def test_generic_fake_chat_model_stream() -> None:
    """Test streaming."""
    infinite_cycle = cycle(
        [
            AIMessage(content="hello goodbye"),
        ]
    )
    model = GenericFakeChatModel(messages=infinite_cycle)
    chunks = [chunk async for chunk in model.astream("meow")]
    assert chunks == [
        _any_id_ai_message_chunk(content="hello"),
        _any_id_ai_message_chunk(content=" "),
        _any_id_ai_message_chunk(content="goodbye", chunk_position="last"),
    ]
    assert len({chunk.id for chunk in chunks}) == 1

    chunks = list(model.stream("meow"))
    assert chunks == [
        _any_id_ai_message_chunk(content="hello"),
        _any_id_ai_message_chunk(content=" "),
        _any_id_ai_message_chunk(content="goodbye", chunk_position="last"),
    ]
    assert len({chunk.id for chunk in chunks}) == 1

    # Test streaming of additional kwargs.
    # Relying on insertion order of the additional kwargs dict
    message = AIMessage(content="", additional_kwargs={"foo": 42, "bar": 24})
    model = GenericFakeChatModel(messages=cycle([message]))
    chunks = [chunk async for chunk in model.astream("meow")]
    assert chunks == [
        _any_id_ai_message_chunk(content="", additional_kwargs={"foo": 42}),
        _any_id_ai_message_chunk(content="", additional_kwargs={"bar": 24}),
        _any_id_ai_message_chunk(content="", chunk_position="last"),
    ]
    assert len({chunk.id for chunk in chunks}) == 1

    message = AIMessage(
        content="",
        additional_kwargs={
            "function_call": {
                "name": "move_file",
                "arguments": '{\n  "source_path": "foo",\n  "'
                'destination_path": "bar"\n}',
            }
        },
    )
    model = GenericFakeChatModel(messages=cycle([message]))
    chunks = [chunk async for chunk in model.astream("meow")]

    assert chunks == [
        _any_id_ai_message_chunk(
            content="",
            additional_kwargs={"function_call": {"name": "move_file"}},
        ),
        _any_id_ai_message_chunk(
            content="",
            additional_kwargs={
                "function_call": {"arguments": '{\n  "source_path": "foo"'},
            },
        ),
        _any_id_ai_message_chunk(
            content="", additional_kwargs={"function_call": {"arguments": ","}}
        ),
        _any_id_ai_message_chunk(
            content="",
            additional_kwargs={
                "function_call": {"arguments": '\n  "destination_path": "bar"\n}'},
            },
        ),
        _any_id_ai_message_chunk(content="", chunk_position="last"),
    ]
    assert len({chunk.id for chunk in chunks}) == 1

    accumulate_chunks = None
    for chunk in chunks:
        if accumulate_chunks is None:
            accumulate_chunks = chunk
        else:
            accumulate_chunks += chunk

    assert accumulate_chunks == AIMessageChunk(
        content="",
        additional_kwargs={
            "function_call": {
                "name": "move_file",
                "arguments": '{\n  "source_path": "foo",\n  "'
                'destination_path": "bar"\n}',
            }
        },
        id=chunks[0].id,
        chunk_position="last",
    )