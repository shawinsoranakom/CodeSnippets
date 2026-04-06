def test_openapi_schema():
    response = client.get("/openapi.json")
    assert response.status_code == 200, response.text
    assert response.json() == snapshot(
        {
            "info": {"title": "FastAPI", "version": "0.1.0"},
            "openapi": "3.1.0",
            "paths": {
                "/a": {
                    "get": {
                        "operationId": "a_a_get",
                        "responses": {
                            "200": {
                                "content": {"application/json": {"schema": {}}},
                                "description": "Successful Response",
                            }
                        },
                        "summary": "A",
                    }
                },
                "/b": {
                    "get": {
                        "operationId": "b_b_get",
                        "responses": {
                            "200": {
                                "content": {"application/json": {"schema": {}}},
                                "description": "Successful Response",
                            }
                        },
                        "summary": "B",
                    }
                },
            },
        }
    )