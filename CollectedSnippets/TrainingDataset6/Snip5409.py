def test_request_validation_error_includes_endpoint_context():
    captured_exception.exception = None
    try:
        client.get("/users/invalid")
    except Exception:
        pass

    assert captured_exception.exception is not None
    error_str = str(captured_exception.exception)
    assert "get_user" in error_str
    assert "/users/" in error_str