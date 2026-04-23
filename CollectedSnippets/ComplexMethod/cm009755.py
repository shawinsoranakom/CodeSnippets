async def test_stream_log_retriever() -> None:
    prompt = (
        SystemMessagePromptTemplate.from_template("You are a nice assistant.")
        + "{documents}"
        + "{question}"
    )
    llm = FakeListLLM(responses=["foo", "bar"])

    chain: Runnable = (
        {"documents": FakeRetriever(), "question": itemgetter("question")}
        | prompt
        | {"one": llm, "two": llm}
    )

    stream_log = [
        part async for part in chain.astream_log({"question": "What is your name?"})
    ]

    # Remove IDs from logs
    for part in stream_log:
        for op in part.ops:
            if (
                isinstance(op["value"], dict)
                and "id" in op["value"]
                and not isinstance(op["value"]["id"], list)  # serialized lc id
            ):
                del op["value"]["id"]

    assert sorted(cast("RunLog", add(stream_log)).state["logs"]) == [
        "ChatPromptTemplate",
        "FakeListLLM",
        "FakeListLLM:2",
        "FakeRetriever",
        "RunnableLambda",
        "RunnableParallel<documents,question>",
        "RunnableParallel<one,two>",
    ]