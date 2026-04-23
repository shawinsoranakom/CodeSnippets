def test_post_body_form_no_data(client: TestClient):
    response = client.post("/login/")
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "missing",
                "loc": ["body", "username"],
                "msg": "Field required",
                "input": None,
            },
            {
                "type": "missing",
                "loc": ["body", "password"],
                "msg": "Field required",
                "input": None,
            },
        ]
    }