async def test_default_method_implementations_async(mocker: MockerFixture) -> None:
    fake = FakeRunnable()
    spy = mocker.spy(fake, "invoke")

    assert await fake.ainvoke("hello", config={"callbacks": []}) == 5
    assert spy.call_args_list == [
        mocker.call("hello", {"callbacks": []}),
    ]
    spy.reset_mock()

    assert [part async for part in fake.astream("hello")] == [5]
    assert spy.call_args_list == [
        mocker.call("hello", None),
    ]
    spy.reset_mock()

    assert await fake.abatch(["hello", "wooorld"], {"metadata": {"key": "value"}}) == [
        5,
        7,
    ]
    assert {call.args[0] for call in spy.call_args_list} == {"hello", "wooorld"}
    for call in spy.call_args_list:
        assert call.args[1] == {
            "metadata": {"key": "value"},
            "tags": [],
            "callbacks": None,
            "recursion_limit": 25,
            "configurable": {},
        }