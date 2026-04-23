def test_get_enums_invalid():
    response = client.get("/models/foo")
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "enum",
                "loc": ["path", "model_name"],
                "msg": "Input should be 'alexnet', 'resnet' or 'lenet'",
                "input": "foo",
                "ctx": {"expected": "'alexnet', 'resnet' or 'lenet'"},
            }
        ]
    }