def test_allow_inf_nan_param_false(value: str, code: int):
    response = client.post(f"/?y={value}")
    assert response.status_code == code, response.text