def test_required_alias_by_alias(path: str):
    client = TestClient(app)
    response = client.post(path, data={"p_alias": "hello"})
    assert response.status_code == 200, response.text
    assert response.json() == {"p": "hello"}