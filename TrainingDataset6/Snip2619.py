def test_explicit_response_class_uses_json_dumps():
    """When response_class is explicitly set to JSONResponse, the normal path
    is used and json.dumps is called via JSONResponse.render()."""
    with patch(
        "starlette.responses.json.dumps", wraps=__import__("json").dumps
    ) as mock_dumps:
        response = client.get("/explicit")
    assert response.status_code == 200
    assert response.json() == {"name": "widget", "price": 9.99}
    mock_dumps.assert_called_once()