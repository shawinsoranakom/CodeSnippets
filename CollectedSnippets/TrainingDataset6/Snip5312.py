def test_lax_post_without_content_type_is_parsed_as_json(client: TestClient):
    response = client.post(
        "/items/",
        content='{"name": "Foo", "price": 50.5}',
    )
    assert response.status_code == 200, response.text
    assert response.json() == {"name": "Foo", "price": 50.5}