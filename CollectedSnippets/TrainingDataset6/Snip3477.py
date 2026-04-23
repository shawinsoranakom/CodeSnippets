def test_optional_list_alias_and_validation_alias_by_validation_alias(path: str):
    client = TestClient(app)
    response = client.post(path, data={"p_val_alias": ["hello", "world"]})
    assert response.status_code == 200, response.text
    assert response.json() == {
        "p": [
            "hello",
            "world",
        ]
    }