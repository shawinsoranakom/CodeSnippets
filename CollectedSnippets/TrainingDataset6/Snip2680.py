def test_form_default_url_encoded():
    response = client.post("/urlencoded", data={"age": ""})
    assert response.status_code == 200
    assert response.text == "null"