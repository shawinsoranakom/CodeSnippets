def test_put_missing_required_in_image(client: TestClient):
    response = client.put(
        "/items/5",
        json={
            "name": "Foo",
            "price": 35.4,
            "image": {"url": "http://example.com/image.png"},
        },
    )
    assert response.status_code == 422, response.text
    assert response.json() == {
        "detail": [
            {
                "loc": ["body", "image", "name"],
                "input": {"url": "http://example.com/image.png"},
                "msg": "Field required",
                "type": "missing",
            },
        ]
    }