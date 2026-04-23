def test_list_alias_and_validation_alias_by_name(path: str):
    client = TestClient(app)
    response = client.post(path, files=[("p", "hello"), ("p", "world")])
    assert response.status_code == 422

    assert response.json() == {
        "detail": [
            {
                "type": "missing",
                "loc": [
                    "body",
                    "p_val_alias",
                ],
                "msg": "Field required",
                "input": None,
            }
        ]
    }