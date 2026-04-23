def test_response_model_has_default_factory_return_dict():
    response = client.get("/response_model_has_default_factory_return_dict")

    assert response.status_code == 200, response.text

    assert response.json()["code"] == 200
    assert response.json()["message"] == "Successful operation."