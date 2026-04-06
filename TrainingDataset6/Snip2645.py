def test_traceback_for_dependency_with_yield():
    client = TestClient(app, raise_server_exceptions=True)
    with pytest.raises(ValueError) as exc_info:
        client.get("/dependency-with-yield")
    last_frame = exc_info.traceback[-1]
    assert str(last_frame.path) == __file__
    assert last_frame.lineno == raise_value_error.__code__.co_firstlineno