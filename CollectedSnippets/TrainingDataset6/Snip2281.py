def test_catching():
    response = client.get("/catching")
    assert response.status_code == 418
    assert response.json() == {"detail": "Session error"}