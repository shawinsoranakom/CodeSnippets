def test_post_broken_body(client: TestClient):
    response = client.post(
        "/items/",
        headers={"content-type": "application/json"},
        content="{some broken json}",
    )
    assert response.status_code == 422, response.text
    assert response.json() == {
        "detail": [
            {
                "type": "json_invalid",
                "loc": ["body", 1],
                "msg": "JSON decode error",
                "input": {},
                "ctx": {"error": "Expecting property name enclosed in double quotes"},
            }
        ]
    }