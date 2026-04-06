def test_subapp_websocket_validation_error_includes_endpoint_context():
    captured_exception.exception = None
    try:
        with client.websocket_connect("/sub/ws/invalid"):
            pass  # pragma: no cover
    except Exception:
        pass

    assert captured_exception.exception is not None
    error_str = str(captured_exception.exception)
    assert "subapp_websocket_endpoint" in error_str
    assert "/sub/ws/" in error_str