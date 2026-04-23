def test_required_list_alias_by_name(path: str):
    client = TestClient(app)
    response = client.post(path, json={"p": ["hello", "world"]})
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "missing",
                "loc": ["body", "p_alias"],
                "msg": "Field required",
                "input": IsOneOf(None, {"p": ["hello", "world"]}),
            }
        ]
    }