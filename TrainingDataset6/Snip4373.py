def test_openapi_schema():
    response = client.get("/openapi.json")
    assert response.status_code == 200, response.text
    assert response.json() == snapshot(
        {
            "openapi": "3.1.0",
            "info": {"title": "FastAPI", "version": "0.1.0"},
            "paths": {
                "/": {
                    "get": {
                        "summary": "Get Root",
                        "operationId": "get_root__get",
                        "responses": {
                            "200": {
                                "description": "Successful Response",
                                "content": {"application/json": {"schema": {}}},
                            }
                        },
                        "security": [{"HTTPBearer": []}],
                    }
                }
            },
            "components": {
                "securitySchemes": {"HTTPBearer": {"type": "http", "scheme": "bearer"}}
            },
        }
    )