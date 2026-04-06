def test_single_form_field():
    response = client.post("/form/", data={"username": "Rick"})
    assert response.status_code == 200, response.text
    assert response.json() == "Rick"