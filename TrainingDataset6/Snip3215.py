def test_model_optional_list_validation_alias_missing():
    client = TestClient(app)
    response = client.post("/model-optional-list-validation-alias")
    assert response.status_code == 422, response.text
    assert response.json() == {
        "detail": [
            {
                "input": None,
                "loc": ["body"],
                "msg": "Field required",
                "type": "missing",
            },
        ],
    }