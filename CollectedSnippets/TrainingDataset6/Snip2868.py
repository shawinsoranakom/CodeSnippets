def test_post(path):
    data = {"a": 2, "b": "foo"}
    response = client.post(path, json=data)
    assert response.status_code == 200, response.text
    assert data == response.json()