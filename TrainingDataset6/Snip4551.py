def test_put_only_required(client: TestClient):
    response = client.post(
        "/offers/",
        json={
            "name": "Special Offer",
            "price": 38.6,
            "items": [
                {
                    "name": "Foo",
                    "price": 35.4,
                    "images": [
                        {
                            "url": "http://example.com/image.png",
                            "name": "example image",
                        }
                    ],
                }
            ],
        },
    )
    assert response.status_code == 200, response.text
    assert response.json() == {
        "name": "Special Offer",
        "description": None,
        "price": 38.6,
        "items": [
            {
                "name": "Foo",
                "description": None,
                "price": 35.4,
                "tax": None,
                "tags": [],
                "images": [
                    {
                        "url": "http://example.com/image.png",
                        "name": "example image",
                    }
                ],
            }
        ],
    }