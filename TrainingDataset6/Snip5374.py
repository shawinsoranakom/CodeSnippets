def test_invalid_form_data():
    response = client.post(
        "/form-union/",
        data={"name": "John", "company_name": "Tech Corp"},
    )
    assert response.status_code == 422, response.text