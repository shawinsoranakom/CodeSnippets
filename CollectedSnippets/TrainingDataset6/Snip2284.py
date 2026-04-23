def test_broken_return_finishes():
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/broken")
    assert response.status_code == 200
    assert response.json() == {"message": "all good?"}