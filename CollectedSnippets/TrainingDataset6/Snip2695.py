def test_extra_param_list():
    response = client.post(
        "/form-extra-allow/",
        data={
            "param": "123",
            "extra_params": ["456", "789"],
        },
    )
    assert response.status_code == 200, response.text
    assert response.json() == {
        "param": "123",
        "extra_params": ["456", "789"],
    }