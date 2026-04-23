def test_required_list_alias_and_validation_alias_missing(path: str):
    client = TestClient(app)
    response = client.get(path)
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "missing",
                "loc": [
                    "header",
                    "p_val_alias",
                ],
                "msg": "Field required",
                "input": AnyThing,
            }
        ]
    }