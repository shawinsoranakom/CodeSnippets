def test_allow_inf_nan_param_true(value: str, code: int):
    response = client.post(f"/?x={value}")
    assert response.status_code == code, response.text