def test_openapi_schema_sub():
    response = client.get("/subapi/openapi.json")
    assert response.status_code == 200, response.text
    assert response.json() == snapshot(
        {
            "openapi": "3.1.0",
            "info": {"title": "FastAPI", "version": "0.1.0"},
            "paths": {
                "/sub": {
                    "get": {
                        "responses": {
                            "200": {
                                "description": "Successful Response",
                                "content": {"application/json": {"schema": {}}},
                            }
                        },
                        "summary": "Read Sub",
                        "operationId": "read_sub_sub_get",
                    }
                }
            },
            "servers": [{"url": "/subapi"}],
        }
    )