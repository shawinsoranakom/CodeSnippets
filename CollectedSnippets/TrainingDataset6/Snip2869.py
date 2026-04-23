def test_post_invalid(path):
    data = {"a": "bar", "b": "foo"}
    response = client.post(path, json=data)
    assert response.status_code == 422, response.text