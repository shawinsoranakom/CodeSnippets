def test_post_body_json(client: TestClient):
    response = client.post("/files/", json={"file": "Foo"})
    assert response.status_code == 422, response.text
    assert response.json() == {
        "detail": [
            {
                "type": "missing",
                "loc": ["body", "files"],
                "msg": "Field required",
                "input": None,
            }
        ]
    }