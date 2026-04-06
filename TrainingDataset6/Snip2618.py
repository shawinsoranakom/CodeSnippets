def test_default_response_class_skips_json_dumps():
    """When no response_class is set, the fast path serializes directly to
    JSON bytes via Pydantic's dump_json and never calls json.dumps."""
    with patch(
        "starlette.responses.json.dumps", wraps=__import__("json").dumps
    ) as mock_dumps:
        response = client.get("/default")
    assert response.status_code == 200
    assert response.json() == {"name": "widget", "price": 9.99}
    mock_dumps.assert_not_called()