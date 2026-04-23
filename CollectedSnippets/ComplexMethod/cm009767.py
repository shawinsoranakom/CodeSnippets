def test_map_stream_iterator_input() -> None:
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

    chain: Runnable = (
        prompt
        | llm
        | {
            "chat": chat.bind(stop=["Thought:"]),
            "llm": llm,
            "passthrough": RunnablePassthrough(),
        }
    )

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
        {"passthrough": "i"},
        {"llm": "i"},
        {"chat": _any_id_ai_message_chunk(content="i")},
    ]
    assert len(streamed_chunks) == len(chat_res) + len(llm_res) + len(llm_res)
    assert all(len(c.keys()) == 1 for c in streamed_chunks)
    assert final_value is not None
    assert final_value.get("chat").content == "i'm a chatbot"
    assert final_value.get("llm") == "i'm a textbot"
    assert final_value.get("passthrough") == "i'm a textbot"