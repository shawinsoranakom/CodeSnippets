def test_extra_param_single():
    response = client.post(
        "/form-extra-allow/",
        data={
            "param": "123",
            "extra_param": "456",
        },
    )
    assert response.status_code == 200, response.text
    assert response.json() == {
        "param": "123",
        "extra_param": "456",
    }