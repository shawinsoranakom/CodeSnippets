def test_put_missing_required_in_images(client: TestClient):
    response = client.post(
        "/offers/",
        json={
            "name": "Special Offer",
            "price": 38.6,
            "items": [
                {"name": "Foo", "price": 35.4, "images": [{}]},
            ],
        },
    )
    assert response.status_code == 422, response.text
    assert response.json() == {
        "detail": [
            {
                "loc": ["body", "items", 0, "images", 0, "url"],
                "input": {},
                "msg": "Field required",
                "type": "missing",
            },
            {
                "loc": ["body", "items", 0, "images", 0, "name"],
                "input": {},
                "msg": "Field required",
                "type": "missing",
            },
        ]
    }