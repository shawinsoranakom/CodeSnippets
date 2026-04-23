def test_send_all_data():
    response = client.post(
        "/form/",
        data={
            "username": "Rick",
            "lastname": "Sanchez",
            "age": "70",
            "tags": ["plumbus", "citadel"],
            "with": "something",
        },
    )
    assert response.status_code == 200, response.text
    assert response.json() == {
        "username": "Rick",
        "lastname": "Sanchez",
        "age": 70,
        "tags": ["plumbus", "citadel"],
        "with": "something",
    }