def test_path_operation(client: TestClient):
    response = client.put(
        "/items/1",
        json={
            "title": "Foo",
            "timestamp": "2023-01-01T12:00:00",
            "description": "A test item",
        },
    )
    assert response.status_code == 200, response.text
    assert response.json() == {
        "description": "A test item",
        "timestamp": "2023-01-01T12:00:00",
        "title": "Foo",
    }