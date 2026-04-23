def test_annotations():
    response = client.get("/item")
    assert response.status_code == 200, response.text
    assert response.json() == snapshot(
        {
            "id": IsUUID(),
            "name": "Island In The Moon",
            "price": 12.99,
            "tags": ["breater"],
            "description": "A place to be playin' and havin' fun",
            "tax": None,
        }
    )