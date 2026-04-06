def test_required_list_alias_missing(path: str):
    client = TestClient(app)
    response = client.get(path)
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "missing",
                "loc": ["query", "p_alias"],
                "msg": "Field required",
                "input": IsOneOf(None, {}),
            }
        ]
    }