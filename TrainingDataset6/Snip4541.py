def test_put_wrong_url(client: TestClient):
    response = client.put(
        "/items/5",
        json={
            "name": "Foo",
            "price": 35.4,
            "image": {"url": "not a valid url", "name": "example image"},
        },
    )
    assert response.status_code == 422, response.text
    assert response.json() == {
        "detail": [
            {
                "loc": ["body", "image", "url"],
                "input": "not a valid url",
                "msg": "Input should be a valid URL, relative URL without a base",
                "type": "url_parsing",
                "ctx": {"error": "relative URL without a base"},
            },
        ]
    }