async def test_map_astream() -> None:
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

    stream = chain.astream({"question": "What is your name?"})

    final_value = None
    streamed_chunks = []
    async for chunk in stream:
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
    final_value["chat"].id = AnyStr()
    assert final_value.get("llm") == "i'm a textbot"
    assert final_value.get("passthrough") == prompt.invoke(
        {"question": "What is your name?"}
    )

    # Test astream_log state accumulation

    final_state = None
    streamed_ops = []
    async for chunk in chain.astream_log({"question": "What is your name?"}):
        streamed_ops.extend(chunk.ops)
        if final_state is None:
            final_state = chunk
        else:
            final_state += chunk
    final_state = cast("RunLog", final_state)

    assert final_state.state["final_output"] == final_value
    assert len(final_state.state["streamed_output"]) == len(streamed_chunks)
    assert isinstance(final_state.state["id"], str)
    assert len(final_state.ops) == len(streamed_ops)
    assert len(final_state.state["logs"]) == 5
    assert (
        final_state.state["logs"]["ChatPromptTemplate"]["name"] == "ChatPromptTemplate"
    )
    assert final_state.state["logs"]["ChatPromptTemplate"][
        "final_output"
    ] == prompt.invoke({"question": "What is your name?"})
    assert (
        final_state.state["logs"]["RunnableParallel<chat,llm,passthrough>"]["name"]
        == "RunnableParallel<chat,llm,passthrough>"
    )
    assert sorted(final_state.state["logs"]) == [
        "ChatPromptTemplate",
        "FakeListChatModel",
        "FakeStreamingListLLM",
        "RunnableParallel<chat,llm,passthrough>",
        "RunnablePassthrough",
    ]

    # Test astream_log with include filters
    final_state = None
    async for chunk in chain.astream_log(
        {"question": "What is your name?"}, include_names=["FakeListChatModel"]
    ):
        if final_state is None:
            final_state = chunk
        else:
            final_state += chunk
    final_state = cast("RunLog", final_state)

    assert final_state.state["final_output"] == final_value
    assert len(final_state.state["streamed_output"]) == len(streamed_chunks)
    assert len(final_state.state["logs"]) == 1
    assert final_state.state["logs"]["FakeListChatModel"]["name"] == "FakeListChatModel"

    # Test astream_log with exclude filters
    final_state = None
    async for chunk in chain.astream_log(
        {"question": "What is your name?"}, exclude_names=["FakeListChatModel"]
    ):
        if final_state is None:
            final_state = chunk
        else:
            final_state += chunk
    final_state = cast("RunLog", final_state)

    assert final_state.state["final_output"] == final_value
    assert len(final_state.state["streamed_output"]) == len(streamed_chunks)
    assert len(final_state.state["logs"]) == 4
    assert (
        final_state.state["logs"]["ChatPromptTemplate"]["name"] == "ChatPromptTemplate"
    )
    assert final_state.state["logs"]["ChatPromptTemplate"]["final_output"] == (
        prompt.invoke({"question": "What is your name?"})
    )
    assert (
        final_state.state["logs"]["RunnableParallel<chat,llm,passthrough>"]["name"]
        == "RunnableParallel<chat,llm,passthrough>"
    )
    assert sorted(final_state.state["logs"]) == [
        "ChatPromptTemplate",
        "FakeStreamingListLLM",
        "RunnableParallel<chat,llm,passthrough>",
        "RunnablePassthrough",
    ]