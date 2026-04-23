async def test_with_config_async(mocker: MockerFixture) -> None:
    fake = FakeRunnable()
    spy = mocker.spy(fake, "invoke")

    handler = ConsoleCallbackHandler()
    assert (
        await fake.with_config(metadata={"a": "b"}).ainvoke(
            "hello", config={"callbacks": [handler]}
        )
        == 5
    )
    assert spy.call_args_list == [
        mocker.call(
            "hello",
            {
                "callbacks": [handler],
                "metadata": {"a": "b"},
                "configurable": {},
                "tags": [],
            },
        ),
    ]
    spy.reset_mock()

    assert [
        part async for part in fake.with_config(metadata={"a": "b"}).astream("hello")
    ] == [5]
    assert spy.call_args_list == [
        mocker.call("hello", {"metadata": {"a": "b"}, "tags": [], "configurable": {}}),
    ]
    spy.reset_mock()

    assert await fake.with_config(recursion_limit=5, tags=["c"]).abatch(
        ["hello", "wooorld"], {"metadata": {"key": "value"}}
    ) == [
        5,
        7,
    ]
    assert sorted(spy.call_args_list) == [
        mocker.call(
            "hello",
            {
                "metadata": {"key": "value"},
                "tags": ["c"],
                "callbacks": None,
                "recursion_limit": 5,
                "configurable": {},
            },
        ),
        mocker.call(
            "wooorld",
            {
                "metadata": {"key": "value"},
                "tags": ["c"],
                "callbacks": None,
                "recursion_limit": 5,
                "configurable": {},
            },
        ),
    ]
    spy.reset_mock()

    assert sorted(
        [
            c
            async for c in fake.with_config(
                recursion_limit=5, tags=["c"]
            ).abatch_as_completed(["hello", "wooorld"], {"metadata": {"key": "value"}})
        ]
    ) == [
        (0, 5),
        (1, 7),
    ]
    assert len(spy.call_args_list) == 2
    first_call = next(call for call in spy.call_args_list if call.args[0] == "hello")
    assert first_call == mocker.call(
        "hello",
        {
            "metadata": {"key": "value"},
            "tags": ["c"],
            "callbacks": None,
            "recursion_limit": 5,
            "configurable": {},
        },
    )
    second_call = next(call for call in spy.call_args_list if call.args[0] == "wooorld")
    assert second_call == mocker.call(
        "wooorld",
        {
            "metadata": {"key": "value"},
            "tags": ["c"],
            "callbacks": None,
            "recursion_limit": 5,
            "configurable": {},
        },
    )