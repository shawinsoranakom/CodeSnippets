def test_with_config(mocker: MockerFixture) -> None:
    fake = FakeRunnable()
    spy = mocker.spy(fake, "invoke")

    assert fake.with_config(tags=["a-tag"]).invoke("hello") == 5
    assert spy.call_args_list == [
        mocker.call(
            "hello",
            {"tags": ["a-tag"], "metadata": {}, "configurable": {}},
        ),
    ]
    spy.reset_mock()

    fake_1 = RunnablePassthrough[Any]()
    fake_2 = RunnablePassthrough[Any]()
    spy_seq_step = mocker.spy(fake_1.__class__, "invoke")

    sequence = fake_1.with_config(tags=["a-tag"]) | fake_2.with_config(
        tags=["b-tag"], max_concurrency=5
    )
    assert sequence.invoke("hello") == "hello"
    assert len(spy_seq_step.call_args_list) == 2
    for i, call in enumerate(spy_seq_step.call_args_list):
        assert call.args[1] == "hello"
        if i == 0:
            assert call.args[2].get("tags") == ["a-tag"]
            assert call.args[2].get("max_concurrency") is None
        else:
            assert call.args[2].get("tags") == ["b-tag"]
            assert call.args[2].get("max_concurrency") == 5
    mocker.stop(spy_seq_step)

    assert [
        *fake.with_config(tags=["a-tag"]).stream(
            "hello", {"metadata": {"key": "value"}}
        )
    ] == [5]
    assert spy.call_args_list == [
        mocker.call(
            "hello",
            {"tags": ["a-tag"], "metadata": {"key": "value"}, "configurable": {}},
        ),
    ]
    spy.reset_mock()

    assert fake.with_config(recursion_limit=5).batch(
        ["hello", "wooorld"], [{"tags": ["a-tag"]}, {"metadata": {"key": "value"}}]
    ) == [5, 7]

    assert len(spy.call_args_list) == 2
    for i, call in enumerate(
        sorted(spy.call_args_list, key=lambda x: 0 if x.args[0] == "hello" else 1)
    ):
        assert call.args[0] == ("hello" if i == 0 else "wooorld")
        if i == 0:
            assert call.args[1].get("recursion_limit") == 5
            assert call.args[1].get("tags") == ["a-tag"]
            assert call.args[1].get("metadata") == {}
        else:
            assert call.args[1].get("recursion_limit") == 5
            assert call.args[1].get("tags") == []
            assert call.args[1].get("metadata") == {"key": "value"}

    spy.reset_mock()

    assert sorted(
        c
        for c in fake.with_config(recursion_limit=5).batch_as_completed(
            ["hello", "wooorld"],
            [{"tags": ["a-tag"]}, {"metadata": {"key": "value"}}],
        )
    ) == [(0, 5), (1, 7)]

    assert len(spy.call_args_list) == 2
    for i, call in enumerate(
        sorted(spy.call_args_list, key=lambda x: 0 if x.args[0] == "hello" else 1)
    ):
        assert call.args[0] == ("hello" if i == 0 else "wooorld")
        if i == 0:
            assert call.args[1].get("recursion_limit") == 5
            assert call.args[1].get("tags") == ["a-tag"]
            assert call.args[1].get("metadata") == {}
        else:
            assert call.args[1].get("recursion_limit") == 5
            assert call.args[1].get("tags") == []
            assert call.args[1].get("metadata") == {"key": "value"}

    spy.reset_mock()

    assert fake.with_config(metadata={"a": "b"}).batch(
        ["hello", "wooorld"], {"tags": ["a-tag"]}
    ) == [5, 7]
    assert len(spy.call_args_list) == 2
    for i, call in enumerate(spy.call_args_list):
        assert call.args[0] == ("hello" if i == 0 else "wooorld")
        assert call.args[1].get("tags") == ["a-tag"]
        assert call.args[1].get("metadata") == {"a": "b"}
    spy.reset_mock()

    assert sorted(
        c for c in fake.batch_as_completed(["hello", "wooorld"], {"tags": ["a-tag"]})
    ) == [(0, 5), (1, 7)]
    assert len(spy.call_args_list) == 2
    for i, call in enumerate(spy.call_args_list):
        assert call.args[0] == ("hello" if i == 0 else "wooorld")
        assert call.args[1].get("tags") == ["a-tag"]