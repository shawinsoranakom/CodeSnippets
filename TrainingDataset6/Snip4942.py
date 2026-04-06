def test_query_param_model_invalid(client: TestClient):
    response = client.get(
        "/items/",
        params={
            "limit": 150,
            "offset": -1,
            "order_by": "invalid",
        },
    )
    assert response.status_code == 422
    assert response.json() == snapshot(
        {
            "detail": [
                {
                    "type": "less_than_equal",
                    "loc": ["query", "limit"],
                    "msg": "Input should be less than or equal to 100",
                    "input": "150",
                    "ctx": {"le": 100},
                },
                {
                    "type": "greater_than_equal",
                    "loc": ["query", "offset"],
                    "msg": "Input should be greater than or equal to 0",
                    "input": "-1",
                    "ctx": {"ge": 0},
                },
                {
                    "type": "literal_error",
                    "loc": ["query", "order_by"],
                    "msg": "Input should be 'created_at' or 'updated_at'",
                    "input": "invalid",
                    "ctx": {"expected": "'created_at' or 'updated_at'"},
                },
            ]
        }
    )