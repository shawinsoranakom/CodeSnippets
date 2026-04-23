def test_post_form_no_body(client: TestClient):
    response = client.post("/files/")
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