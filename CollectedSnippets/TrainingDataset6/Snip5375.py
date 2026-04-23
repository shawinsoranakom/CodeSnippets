def test_empty_form():
    response = client.post("/form-union/")
    assert response.status_code == 422, response.text