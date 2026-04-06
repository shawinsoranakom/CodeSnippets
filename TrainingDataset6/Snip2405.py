def test_no_duplicates_invalid():
    response = client.post("/no-duplicates", json={"item": {"data": "myitem"}})
    assert response.status_code == 422, response.text
    assert response.json() == {
        "detail": [
            {
                "type": "missing",
                "loc": ["body", "item2"],
                "msg": "Field required",
                "input": None,
            }
        ]
    }