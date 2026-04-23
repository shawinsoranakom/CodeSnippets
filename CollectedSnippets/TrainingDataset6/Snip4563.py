def test_post_invalid_body(client: TestClient):
    data = {"foo": 2.2, "3": 3.3}
    response = client.post("/index-weights/", json=data)
    assert response.status_code == 422, response.text
    assert response.json() == {
        "detail": [
            {
                "type": "int_parsing",
                "loc": ["body", "foo", "[key]"],
                "msg": "Input should be a valid integer, unable to parse string as an integer",
                "input": "foo",
            }
        ]
    }