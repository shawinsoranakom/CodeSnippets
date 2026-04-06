def test_websocket_validation_error_includes_endpoint_context():
    captured_exception.exception = None
    try:
        with client.websocket_connect("/ws/invalid"):
            pass  # pragma: no cover
    except Exception:
        pass

    assert captured_exception.exception is not None
    error_str = str(captured_exception.exception)
    assert "websocket_endpoint" in error_str
    assert "/ws/" in error_str