def test_stream_json_validation_error_async():
    with pytest.raises(ResponseValidationError):
        client.get("/items/stream-invalid")