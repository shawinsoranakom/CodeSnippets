def test_required_alias_by_name(path: str):
    client = TestClient(app)
    response = client.post(path, json={"p": "hello"})
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "missing",
                "loc": ["body", "p_alias"],
                "msg": "Field required",
                "input": IsOneOf(None, {"p": "hello"}),
            }
        ]
    }