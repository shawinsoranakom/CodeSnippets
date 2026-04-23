def test_read_admin():
    response = client.get("/admin", headers={"Authorization": "Bearer faketoken"})
    assert response.status_code == 200, response.text
    assert response.json() == {"message": "Admin Access"}