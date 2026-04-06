def test_wrong_headers(client: TestClient):
    data = '{"name": "Foo", "price": 50.5}'
    response = client.post(
        "/items/", content=data, headers={"Content-Type": "text/plain"}
    )
    assert response.status_code == 422, response.text
    assert response.json() == {
        "detail": [
            {
                "type": "model_attributes_type",
                "loc": ["body"],
                "msg": "Input should be a valid dictionary or object to extract fields from",
                "input": '{"name": "Foo", "price": 50.5}',
            }
        ]
    }

    response = client.post(
        "/items/", content=data, headers={"Content-Type": "application/geo+json-seq"}
    )
    assert response.status_code == 422, response.text
    assert response.json() == {
        "detail": [
            {
                "type": "model_attributes_type",
                "loc": ["body"],
                "msg": "Input should be a valid dictionary or object to extract fields from",
                "input": '{"name": "Foo", "price": 50.5}',
            }
        ]
    }

    response = client.post(
        "/items/", content=data, headers={"Content-Type": "application/not-really-json"}
    )
    assert response.status_code == 422, response.text
    assert response.json() == {
        "detail": [
            {
                "type": "model_attributes_type",
                "loc": ["body"],
                "msg": "Input should be a valid dictionary or object to extract fields from",
                "input": '{"name": "Foo", "price": 50.5}',
            }
        ]
    }