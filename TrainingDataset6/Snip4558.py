def test_post_invalid_list_item(client: TestClient):
    data = [{"url": "not a valid url", "name": "Example"}]
    response = client.post("/images/multiple", json=data)
    assert response.status_code == 422, response.text
    assert response.json() == {
        "detail": [
            {
                "loc": ["body", 0, "url"],
                "input": "not a valid url",
                "msg": "Input should be a valid URL, relative URL without a base",
                "type": "url_parsing",
                "ctx": {"error": "relative URL without a base"},
            },
        ]
    }