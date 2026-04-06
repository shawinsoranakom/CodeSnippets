def test_post_all(client: TestClient):
    data = {
        "name": "Special Offer",
        "description": "This is a special offer",
        "price": 38.6,
        "items": [
            {
                "name": "Foo",
                "description": "A very nice Item",
                "price": 35.4,
                "tax": 3.2,
                "tags": ["foo"],
                "images": [
                    {
                        "url": "http://example.com/image.png",
                        "name": "example image",
                    }
                ],
            }
        ],
    }

    response = client.post(
        "/offers/",
        json=data,
    )
    assert response.status_code == 200, response.text
    assert response.json() == data