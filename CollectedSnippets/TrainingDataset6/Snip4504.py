def test_post_body_no_data(client: TestClient):
    response = client.put("/items/5", json=None)
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "missing",
                "loc": ["body", "item"],
                "msg": "Field required",
                "input": None,
            },
            {
                "type": "missing",
                "loc": ["body", "user"],
                "msg": "Field required",
                "input": None,
            },
            {
                "type": "missing",
                "loc": ["body", "importance"],
                "msg": "Field required",
                "input": None,
            },
        ]
    }