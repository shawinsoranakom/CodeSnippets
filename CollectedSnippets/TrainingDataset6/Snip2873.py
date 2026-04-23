def test_jsonable_encoder_requiring_error():
    response = client.post("/items/", json=[{"name": "Foo", "age": -1.0}])
    assert response.status_code == 422, response.text
    assert response.json() == {
        "detail": [
            {
                "type": "greater_than",
                "loc": ["body", 0, "age"],
                "msg": "Input should be greater than 0",
                "input": -1.0,
                "ctx": {"gt": 0},
            }
        ]
    }