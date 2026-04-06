def test_get_me(client: TestClient):
    response = client.get("/me", headers={"Authorization": "Bearer secrettoken"})
    assert response.status_code == 200
    assert response.json() == {
        "message": "You are authenticated",
        "token": "secrettoken",
    }