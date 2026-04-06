def test_no_content_type_json(client: TestClient):
    response = client.post(
        "/items/",
        content='{"name": "Foo", "price": 50.5}',
    )
    assert response.status_code == 422, response.text