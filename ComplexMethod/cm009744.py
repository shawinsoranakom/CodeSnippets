async def test_passthrough_tap_async(mocker: MockerFixture) -> None:
    fake = FakeRunnable()
    mock = mocker.Mock()

    seq = RunnablePassthrough[Any](mock) | fake | RunnablePassthrough[Any](mock)

    assert await seq.ainvoke("hello", my_kwarg="value") == 5
    assert mock.call_args_list == [
        mocker.call("hello", my_kwarg="value"),
        mocker.call(5),
    ]
    mock.reset_mock()

    assert await seq.abatch(["hello", "byebye"], my_kwarg="value") == [5, 6]
    assert len(mock.call_args_list) == 4
    for call in [
        mocker.call("hello", my_kwarg="value"),
        mocker.call("byebye", my_kwarg="value"),
        mocker.call(5),
        mocker.call(6),
    ]:
        assert call in mock.call_args_list
    mock.reset_mock()

    assert await seq.abatch(
        ["hello", "byebye"], my_kwarg="value", return_exceptions=True
    ) == [
        5,
        6,
    ]
    assert len(mock.call_args_list) == 4
    for call in [
        mocker.call("hello", my_kwarg="value"),
        mocker.call("byebye", my_kwarg="value"),
        mocker.call(5),
        mocker.call(6),
    ]:
        assert call in mock.call_args_list
    mock.reset_mock()

    assert sorted(
        [
            a
            async for a in seq.abatch_as_completed(
                ["hello", "byebye"], my_kwarg="value", return_exceptions=True
            )
        ]
    ) == [
        (0, 5),
        (1, 6),
    ]
    assert len(mock.call_args_list) == 4
    for call in [
        mocker.call("hello", my_kwarg="value"),
        mocker.call("byebye", my_kwarg="value"),
        mocker.call(5),
        mocker.call(6),
    ]:
        assert call in mock.call_args_list
    mock.reset_mock()

    assert [
        part
        async for part in seq.astream(
            "hello", {"metadata": {"key": "value"}}, my_kwarg="value"
        )
    ] == [5]
    assert mock.call_args_list == [
        mocker.call("hello", my_kwarg="value"),
        mocker.call(5),
    ]