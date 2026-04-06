def test_query(client: TestClient):
    response = client.post("/graphql", json={"query": "{ user { name, age } }"})
    assert response.status_code == 200
    assert response.json() == {"data": {"user": {"name": "Patrick", "age": 100}}}