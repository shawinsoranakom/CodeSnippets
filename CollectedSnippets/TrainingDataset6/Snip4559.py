def test_post_not_a_list(client: TestClient):
    data = {"url": "http://example.com/", "name": "Example"}
    response = client.post("/images/multiple", json=data)
    assert response.status_code == 422, response.text
    assert response.json() == {
        "detail": [
            {
                "loc": ["body"],
                "input": {
                    "name": "Example",
                    "url": "http://example.com/",
                },
                "msg": "Input should be a valid list",
                "type": "list_type",
            }
        ]
    }