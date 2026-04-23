def test_seq_dict_prompt_llm(
    mocker: MockerFixture, snapshot: SnapshotAssertion
) -> None:
    passthrough = mocker.Mock(side_effect=lambda x: x)

    retriever = FakeRetriever()

    prompt = (
        SystemMessagePromptTemplate.from_template("You are a nice assistant.")
        + """Context:
{documents}

Question:
{question}"""
    )

    chat = FakeListChatModel(responses=["foo, bar"])

    parser = CommaSeparatedListOutputParser()

    chain: Runnable = (
        {
            "question": RunnablePassthrough[str]() | passthrough,
            "documents": passthrough | retriever,
            "just_to_test_lambda": passthrough,
        }
        | prompt
        | chat
        | parser
    )

    assert repr(chain) == snapshot
    assert isinstance(chain, RunnableSequence)
    assert isinstance(chain.first, RunnableParallel)
    assert chain.middle == [prompt, chat]
    assert chain.last == parser
    assert dumps(chain, pretty=True) == snapshot

    # Test invoke
    prompt_spy = mocker.spy(prompt.__class__, "invoke")
    chat_spy = mocker.spy(chat.__class__, "invoke")
    parser_spy = mocker.spy(parser.__class__, "invoke")
    tracer = FakeTracer()
    assert chain.invoke("What is your name?", {"callbacks": [tracer]}) == [
        "foo",
        "bar",
    ]
    assert prompt_spy.call_args.args[1] == {
        "documents": [Document(page_content="foo"), Document(page_content="bar")],
        "question": "What is your name?",
        "just_to_test_lambda": "What is your name?",
    }
    assert chat_spy.call_args.args[1] == ChatPromptValue(
        messages=[
            SystemMessage(
                content="You are a nice assistant.",
                additional_kwargs={},
                response_metadata={},
            ),
            HumanMessage(
                content="Context:\n"
                "[Document(metadata={}, page_content='foo'), "
                "Document(metadata={}, page_content='bar')]\n"
                "\n"
                "Question:\n"
                "What is your name?",
                additional_kwargs={},
                response_metadata={},
            ),
        ]
    )
    assert parser_spy.call_args.args[1] == _any_id_ai_message(content="foo, bar")
    assert len([r for r in tracer.runs if r.parent_run_id is None]) == 1
    parent_run = next(r for r in tracer.runs if r.parent_run_id is None)
    assert len(parent_run.child_runs) == 4
    map_run = parent_run.child_runs[0]
    assert map_run.name == "RunnableParallel<question,documents,just_to_test_lambda>"
    assert len(map_run.child_runs) == 3