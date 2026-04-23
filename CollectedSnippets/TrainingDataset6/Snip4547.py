def test_put_images_not_list(client: TestClient):
    response = client.put(
        "/items/5",
        json={
            "name": "Foo",
            "price": 35.4,
            "images": {"url": "http://example.com/image.png", "name": "example image"},
        },
    )
    assert response.status_code == 422, response.text
    assert response.json() == {
        "detail": [
            {
                "loc": ["body", "images"],
                "input": {
                    "url": "http://example.com/image.png",
                    "name": "example image",
                },
                "msg": "Input should be a valid list",
                "type": "list_type",
            },
        ]
    }