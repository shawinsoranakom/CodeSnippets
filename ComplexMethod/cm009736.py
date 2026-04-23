async def test_input_messages_async() -> None:
    runnable = RunnableLambda[Any, str](
        lambda messages: (
            "you said: "
            + "\n".join(str(m.content) for m in messages if isinstance(m, HumanMessage))
        )
    )
    store: dict[str, InMemoryChatMessageHistory] = {}
    get_session_history = _get_get_session_history(store=store)
    with_history = RunnableWithMessageHistory(runnable, get_session_history)
    config = {"session_id": "1_async"}
    output = await with_history.ainvoke([HumanMessage(content="hello")], config)  # type: ignore[arg-type]
    assert output == "you said: hello"
    output = await with_history.ainvoke([HumanMessage(content="good bye")], config)  # type: ignore[arg-type]
    assert output == "you said: hello\ngood bye"
    output = [
        c
        async for c in with_history.astream([HumanMessage(content="hi again")], config)  # type: ignore[arg-type]
    ]
    assert output == ["you said: hello\ngood bye\nhi again"]
    assert store == {
        "1_async": InMemoryChatMessageHistory(
            messages=[
                HumanMessage(content="hello"),
                AIMessage(content="you said: hello"),
                HumanMessage(content="good bye"),
                AIMessage(content="you said: hello\ngood bye"),
                HumanMessage(content="hi again"),
                AIMessage(content="you said: hello\ngood bye\nhi again"),
            ]
        )
    }