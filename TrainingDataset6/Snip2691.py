def test_defaults():
    response = client.post("/form/", data={"username": "Rick", "lastname": "Sanchez"})
    assert response.status_code == 200, response.text
    assert response.json() == {
        "username": "Rick",
        "lastname": "Sanchez",
        "age": None,
        "tags": ["foo", "bar"],
        "with": "nothing",
    }