def test_lax_post_with_text_plain_is_still_rejected(client: TestClient):
    response = client.post(
        "/items/",
        content='{"name": "Foo", "price": 50.5}',
        headers={"Content-Type": "text/plain"},
    )
    assert response.status_code == 422, response.text