def test_openapi_schema(client: TestClient):
    response = client.get("/openapi.json")
    assert response.status_code == 200, response.text
    assert response.json() == snapshot(
        {
            "openapi": "3.1.0",
            "info": {"title": "FastAPI", "version": "0.1.0"},
            "paths": {
                "/me": {
                    "get": {
                        "summary": "Read Me",
                        "operationId": "read_me_me_get",
                        "responses": {
                            "200": {
                                "description": "Successful Response",
                                "content": {"application/json": {"schema": {}}},
                            }
                        },
                        "security": [{"HTTPBearer403": []}],
                    }
                }
            },
            "components": {
                "securitySchemes": {
                    "HTTPBearer403": {"type": "http", "scheme": "bearer"}
                }
            },
        }
    )