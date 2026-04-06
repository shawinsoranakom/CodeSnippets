def test_allow_inf_nan_param_default(value: str, code: int):
    response = client.post(f"/?z={value}")
    assert response.status_code == code, response.text