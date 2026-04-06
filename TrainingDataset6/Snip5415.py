def test_validation_error_with_no_context():
    errors = [{"type": "missing", "loc": ("body", "name"), "msg": "Field required"}]
    exc = RequestValidationError(errors, endpoint_ctx={})
    error_str = str(exc)
    assert "1 validation error:" in error_str
    assert "Endpoint" not in error_str
    assert 'File "' not in error_str