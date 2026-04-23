def test_allow_inf_nan_body(value: str, code: int):
    response = client.post("/", json=value)
    assert response.status_code == code, response.text