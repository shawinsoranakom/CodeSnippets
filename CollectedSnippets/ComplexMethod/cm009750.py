def test_with_listener_propagation(mocker: MockerFixture) -> None:
    prompt = (
        SystemMessagePromptTemplate.from_template("You are a nice assistant.")
        + "{question}"
    )
    chat = FakeListChatModel(responses=["foo"])
    chain: Runnable = prompt | chat
    mock_start = mocker.Mock()
    mock_end = mocker.Mock()
    chain_with_listeners = chain.with_listeners(on_start=mock_start, on_end=mock_end)

    chain_with_listeners.with_retry().invoke({"question": "Who are you?"})

    assert mock_start.call_count == 1
    assert mock_start.call_args[0][0].name == "RunnableSequence"
    assert mock_end.call_count == 1

    mock_start.reset_mock()
    mock_end.reset_mock()

    chain_with_listeners.with_types(output_type=str).invoke(
        {"question": "Who are you?"}
    )

    assert mock_start.call_count == 1
    assert mock_start.call_args[0][0].name == "RunnableSequence"
    assert mock_end.call_count == 1

    mock_start.reset_mock()
    mock_end.reset_mock()

    chain_with_listeners.with_config({"tags": ["foo"]}).invoke(
        {"question": "Who are you?"}
    )

    assert mock_start.call_count == 1
    assert mock_start.call_args[0][0].name == "RunnableSequence"
    assert mock_end.call_count == 1

    mock_start.reset_mock()
    mock_end.reset_mock()

    chain_with_listeners.bind(stop=["foo"]).invoke({"question": "Who are you?"})

    assert mock_start.call_count == 1
    assert mock_start.call_args[0][0].name == "RunnableSequence"
    assert mock_end.call_count == 1

    mock_start.reset_mock()
    mock_end.reset_mock()

    mock_start_inner = mocker.Mock()
    mock_end_inner = mocker.Mock()

    chain_with_listeners.with_listeners(
        on_start=mock_start_inner, on_end=mock_end_inner
    ).invoke({"question": "Who are you?"})

    assert mock_start.call_count == 1
    assert mock_start.call_args[0][0].name == "RunnableSequence"
    assert mock_end.call_count == 1
    assert mock_start_inner.call_count == 1
    assert mock_start_inner.call_args[0][0].name == "RunnableSequence"
    assert mock_end_inner.call_count == 1