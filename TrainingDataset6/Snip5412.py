def test_subapp_request_validation_error_includes_endpoint_context():
    captured_exception.exception = None
    try:
        client.get("/sub/items/")
    except Exception:
        pass

    assert captured_exception.exception is not None
    error_str = str(captured_exception.exception)
    assert "get_sub_item" in error_str
    assert "/sub/items/" in error_str