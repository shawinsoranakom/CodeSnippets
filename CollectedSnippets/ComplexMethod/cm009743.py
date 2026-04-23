def test_passthrough_tap(mocker: MockerFixture) -> None:
    fake = FakeRunnable()
    mock = mocker.Mock()

    seq = RunnablePassthrough[Any](mock) | fake | RunnablePassthrough[Any](mock)

    assert seq.invoke("hello", my_kwarg="value") == 5
    assert mock.call_args_list == [
        mocker.call("hello", my_kwarg="value"),
        mocker.call(5),
    ]
    mock.reset_mock()

    assert seq.batch(["hello", "byebye"], my_kwarg="value") == [5, 6]
    assert len(mock.call_args_list) == 4
    for call in [
        mocker.call("hello", my_kwarg="value"),
        mocker.call("byebye", my_kwarg="value"),
        mocker.call(5),
        mocker.call(6),
    ]:
        assert call in mock.call_args_list
    mock.reset_mock()

    assert seq.batch(["hello", "byebye"], my_kwarg="value", return_exceptions=True) == [
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
        a
        for a in seq.batch_as_completed(
            ["hello", "byebye"], my_kwarg="value", return_exceptions=True
        )
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

    assert list(
        seq.stream("hello", {"metadata": {"key": "value"}}, my_kwarg="value")
    ) == [5]
    assert mock.call_args_list == [
        mocker.call("hello", my_kwarg="value"),
        mocker.call(5),
    ]
    mock.reset_mock()