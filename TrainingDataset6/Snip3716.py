def test_required_validation_alias_by_name(path: str):
    client = TestClient(app)
    response = client.get(f"{path}?p=hello")
    assert response.status_code == 422, response.text

    assert response.json() == {
        "detail": [
            {
                "type": "missing",
                "loc": ["query", "p_val_alias"],
                "msg": "Field required",
                "input": IsOneOf(None, {"p": "hello"}),
            }
        ]
    }