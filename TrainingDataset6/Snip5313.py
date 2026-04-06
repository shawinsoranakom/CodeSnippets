def test_lax_post_with_json_content_type(client: TestClient):
    response = client.post(
        "/items/",
        json={"name": "Foo", "price": 50.5},
    )
    assert response.status_code == 200, response.text
    assert response.json() == {"name": "Foo", "price": 50.5}