def test_required_alias_and_validation_alias_by_alias(path: str):
    client = TestClient(app)
    client.cookies.set("p_alias", "hello")
    response = client.get(path)
    assert response.status_code == 422

    assert response.json() == {
        "detail": [
            {
                "type": "missing",
                "loc": ["cookie", "p_val_alias"],
                "msg": "Field required",
                "input": IsOneOf(
                    None,
                    {"p_alias": "hello"},
                ),
            }
        ]
    }