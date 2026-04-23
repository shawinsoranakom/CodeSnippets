def test_required_str_missing(path: str):
    client = TestClient(app)
    response = client.get(path)
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "missing",
                "loc": ["query", "p"],
                "msg": "Field required",
                "input": IsOneOf(None, {}),
            }
        ]
    }