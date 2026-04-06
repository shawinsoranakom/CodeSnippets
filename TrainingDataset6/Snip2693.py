def test_no_data():
    response = client.post("/form/")
    assert response.status_code == 422, response.text
    assert response.json() == {
        "detail": [
            {
                "type": "missing",
                "loc": ["body", "username"],
                "msg": "Field required",
                "input": {"tags": ["foo", "bar"], "with": "nothing"},
            },
            {
                "type": "missing",
                "loc": ["body", "lastname"],
                "msg": "Field required",
                "input": {"tags": ["foo", "bar"], "with": "nothing"},
            },
        ]
    }