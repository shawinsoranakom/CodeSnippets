def test_map_stream() -> None:
    prompt = (
        SystemMessagePromptTemplate.from_template("You are a nice assistant.")
        + "{question}"
    )

    chat_res = "i'm a chatbot"
    # sleep to better simulate a real stream
    chat = FakeListChatModel(responses=[chat_res], sleep=0.01)

    llm_res = "i'm a textbot"
    # sleep to better simulate a real stream
    llm = FakeStreamingListLLM(responses=[llm_res], sleep=0.01)

    chain: Runnable = prompt | {
        "chat": chat.bind(stop=["Thought:"]),
        "llm": llm,
        "passthrough": RunnablePassthrough(),
    }

    stream = chain.stream({"question": "What is your name?"})

    final_value = None
    streamed_chunks = []
    for chunk in stream:
        streamed_chunks.append(chunk)
        if final_value is None:
            final_value = chunk
        else:
            final_value += chunk

    assert streamed_chunks[0] in [
        {"passthrough": prompt.invoke({"question": "What is your name?"})},
        {"llm": "i"},
        {"chat": _any_id_ai_message_chunk(content="i")},
    ]
    assert len(streamed_chunks) == len(chat_res) + len(llm_res) + 1
    assert all(len(c.keys()) == 1 for c in streamed_chunks)
    assert final_value is not None
    assert final_value.get("chat").content == "i'm a chatbot"
    assert final_value.get("llm") == "i'm a textbot"
    assert final_value.get("passthrough") == prompt.invoke(
        {"question": "What is your name?"}
    )

    chain_pick_one = chain.pick("llm")

    assert chain_pick_one.get_output_jsonschema() == {
        "title": "RunnableSequenceOutput",
        "type": "string",
    }

    stream = chain_pick_one.stream({"question": "What is your name?"})

    final_value = None
    streamed_chunks = []
    for chunk in stream:
        streamed_chunks.append(chunk)
        if final_value is None:
            final_value = chunk
        else:
            final_value += chunk

    assert streamed_chunks[0] == "i"
    assert len(streamed_chunks) == len(llm_res)

    chain_pick_two = chain.assign(hello=RunnablePick("llm").pipe(llm)).pick(
        [
            "llm",
            "hello",
        ]
    )

    assert chain_pick_two.get_output_jsonschema() == {
        "title": "RunnableSequenceOutput",
        "type": "object",
        "properties": {
            "hello": {"title": "Hello", "type": "string"},
            "llm": {"title": "Llm", "type": "string"},
        },
        "required": ["llm", "hello"],
    }

    stream = chain_pick_two.stream({"question": "What is your name?"})

    final_value = None
    streamed_chunks = []
    for chunk in stream:
        streamed_chunks.append(chunk)
        if final_value is None:
            final_value = chunk
        else:
            final_value += chunk

    assert streamed_chunks[0] in [
        {"llm": "i"},
        {"chat": _any_id_ai_message_chunk(content="i")},
    ]
    if not (
        # TODO: Rewrite properly the statement above
        streamed_chunks[0] == {"llm": "i"}
        or {"chat": _any_id_ai_message_chunk(content="i")}
    ):
        msg = f"Got an unexpected chunk: {streamed_chunks[0]}"
        raise AssertionError(msg)

    assert len(streamed_chunks) == len(llm_res) + len(chat_res)