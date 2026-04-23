def test_required_list_alias_missing(path: str, json: dict | None):
    client = TestClient(app)
    response = client.post(path, json=json)
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "missing",
                "loc": IsOneOf(["body", "p_alias"], ["body"]),
                "msg": "Field required",
                "input": IsOneOf(None, {}),
            }
        ]
    }