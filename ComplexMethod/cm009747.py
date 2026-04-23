def test_default_method_implementations(mocker: MockerFixture) -> None:
    fake = FakeRunnable()
    spy = mocker.spy(fake, "invoke")

    assert fake.invoke("hello", {"tags": ["a-tag"]}) == 5
    assert spy.call_args_list == [
        mocker.call("hello", {"tags": ["a-tag"]}),
    ]
    spy.reset_mock()

    assert [*fake.stream("hello", {"metadata": {"key": "value"}})] == [5]
    assert spy.call_args_list == [
        mocker.call("hello", {"metadata": {"key": "value"}}),
    ]
    spy.reset_mock()

    assert fake.batch(
        ["hello", "wooorld"], [{"tags": ["a-tag"]}, {"metadata": {"key": "value"}}]
    ) == [5, 7]

    assert len(spy.call_args_list) == 2
    for call in spy.call_args_list:
        call_arg = call.args[0]

        if call_arg == "hello":
            assert call_arg == "hello"
            assert call.args[1].get("tags") == ["a-tag"]
            assert call.args[1].get("metadata") == {}
        else:
            assert call_arg == "wooorld"
            assert call.args[1].get("tags") == []
            assert call.args[1].get("metadata") == {"key": "value"}

    spy.reset_mock()

    assert fake.batch(["hello", "wooorld"], {"tags": ["a-tag"]}) == [5, 7]
    assert len(spy.call_args_list) == 2
    assert {call.args[0] for call in spy.call_args_list} == {"hello", "wooorld"}
    for call in spy.call_args_list:
        assert call.args[1].get("tags") == ["a-tag"]
        assert call.args[1].get("metadata") == {}