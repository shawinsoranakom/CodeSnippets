def test_deep_stream_assign() -> None:
    prompt = (
        SystemMessagePromptTemplate.from_template("You are a nice assistant.")
        + "{question}"
    )
    llm = FakeStreamingListLLM(responses=["foo-lish"])

    chain: Runnable = prompt | llm | {"str": StrOutputParser()}

    stream = chain.stream({"question": "What up"})

    chunks = list(stream)

    assert len(chunks) == len("foo-lish")
    assert add(chunks) == {"str": "foo-lish"}

    chain_with_assign = chain.assign(hello=itemgetter("str") | llm)

    assert chain_with_assign.get_input_jsonschema() == {
        "title": "PromptInput",
        "type": "object",
        "properties": {"question": {"title": "Question", "type": "string"}},
        "required": ["question"],
    }
    assert chain_with_assign.get_output_jsonschema() == {
        "title": "RunnableSequenceOutput",
        "type": "object",
        "properties": {
            "str": {"title": "Str", "type": "string"},
            "hello": {"title": "Hello", "type": "string"},
        },
        "required": ["str", "hello"],
    }

    chunks = []
    for chunk in chain_with_assign.stream({"question": "What up"}):
        chunks.append(chunk)

    assert len(chunks) == len("foo-lish") * 2
    assert chunks == [
        # first stream passthrough input chunks
        {"str": "f"},
        {"str": "o"},
        {"str": "o"},
        {"str": "-"},
        {"str": "l"},
        {"str": "i"},
        {"str": "s"},
        {"str": "h"},
        # then stream assign output chunks
        {"hello": "f"},
        {"hello": "o"},
        {"hello": "o"},
        {"hello": "-"},
        {"hello": "l"},
        {"hello": "i"},
        {"hello": "s"},
        {"hello": "h"},
    ]
    assert add(chunks) == {"str": "foo-lish", "hello": "foo-lish"}
    assert chain_with_assign.invoke({"question": "What up"}) == {
        "str": "foo-lish",
        "hello": "foo-lish",
    }

    chain_with_assign_shadow = chain.assign(
        str=lambda _: "shadow",
        hello=itemgetter("str") | llm,
    )

    assert chain_with_assign_shadow.get_input_jsonschema() == {
        "title": "PromptInput",
        "type": "object",
        "properties": {"question": {"title": "Question", "type": "string"}},
        "required": ["question"],
    }
    assert chain_with_assign_shadow.get_output_jsonschema() == {
        "title": "RunnableSequenceOutput",
        "type": "object",
        "properties": {
            "str": {"title": "Str"},
            "hello": {"title": "Hello", "type": "string"},
        },
        "required": ["str", "hello"],
    }

    chunks = []
    for chunk in chain_with_assign_shadow.stream({"question": "What up"}):
        chunks.append(chunk)

    assert len(chunks) == len("foo-lish") + 1
    assert add(chunks) == {"str": "shadow", "hello": "foo-lish"}
    assert chain_with_assign_shadow.invoke({"question": "What up"}) == {
        "str": "shadow",
        "hello": "foo-lish",
    }