def test_lax_outer_accepts_json_content_type():
    response = client_mixed.post("/outer/items/", json={"key": "value"})
    assert response.status_code == 200