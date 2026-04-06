def test_list_alias_and_validation_alias_by_alias(path: str):
    client = TestClient(app)
    response = client.post(path, files=[("p_alias", b"hello"), ("p_alias", b"world")])
    assert response.status_code == 422, response.text

    assert response.json() == {
        "detail": [
            {
                "type": "missing",
                "loc": ["body", "p_val_alias"],
                "msg": "Field required",
                "input": None,
            }
        ]
    }