def test_stream_json_validation_error_sync():
    with pytest.raises(ResponseValidationError):
        client.get("/items/stream-invalid-sync")