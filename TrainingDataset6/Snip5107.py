def test_post_form_no_file(client: TestClient):
    response = client.post("/files/", data={"token": "foo"})
    assert response.status_code == 422, response.text
    assert response.json() == {
        "detail": [
            {
                "type": "missing",
                "loc": ["body", "file"],
                "msg": "Field required",
                "input": None,
            },
            {
                "type": "missing",
                "loc": ["body", "fileb"],
                "msg": "Field required",
                "input": None,
            },
        ]
    }