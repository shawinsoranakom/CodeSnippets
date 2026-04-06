def test_model_optional_list_alias_missing():
    client = TestClient(app)
    response = client.post("/model-optional-list-alias")
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