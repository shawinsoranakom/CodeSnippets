def test_class_dependency(route):
    response = client.get(route)
    assert response.status_code == 200, response.text
    assert response.json() is True