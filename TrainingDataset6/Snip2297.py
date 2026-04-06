def test_broken_session_data_no_raise():
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/broken-session-data")
    assert response.status_code == 500
    assert response.text == "Internal Server Error"