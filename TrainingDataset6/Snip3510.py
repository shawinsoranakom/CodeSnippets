def test_required_alias_missing(path: str):
    client = TestClient(app)
    response = client.post(path)
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "missing",
                "loc": ["body", "p_alias"],
                "msg": "Field required",
                "input": IsOneOf(None, {}),
            }
        ]
    }