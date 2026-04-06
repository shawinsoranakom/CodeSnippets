def test_required_list_alias_and_validation_alias_by_validation_alias(path: str):
    client = TestClient(app)
    response = client.get(
        path, headers=[("p_val_alias", "hello"), ("p_val_alias", "world")]
    )
    assert response.status_code == 200, response.text
    assert response.json() == {"p": ["hello", "world"]}