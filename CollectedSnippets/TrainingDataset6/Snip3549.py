def test_required_list_alias_and_validation_alias_by_alias(path: str):
    client = TestClient(app)
    response = client.get(path, headers=[("p_alias", "hello"), ("p_alias", "world")])
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "missing",
                "loc": ["header", "p_val_alias"],
                "msg": "Field required",
                "input": IsOneOf(
                    None,
                    IsPartialDict({"p_alias": ["hello", "world"]}),
                ),
            }
        ]
    }