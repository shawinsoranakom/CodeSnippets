def test_response_validation_error_includes_endpoint_context():
    captured_exception.exception = None
    try:
        client.get("/items/")
    except Exception:
        pass

    assert captured_exception.exception is not None
    error_str = str(captured_exception.exception)
    assert "get_item" in error_str
    assert "/items/" in error_str