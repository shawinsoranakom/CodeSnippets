def test_validation_error_with_only_path():
    errors = [{"type": "missing", "loc": ("body", "name"), "msg": "Field required"}]
    exc = RequestValidationError(errors, endpoint_ctx={"path": "GET /api/test"})
    error_str = str(exc)
    assert "Endpoint: GET /api/test" in error_str
    assert 'File "' not in error_str