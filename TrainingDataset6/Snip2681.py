def test_form_default_multi_part():
    response = client.post("/multipart", data={"age": ""})
    assert response.status_code == 200
    assert response.json() == {"file": None, "age": None}