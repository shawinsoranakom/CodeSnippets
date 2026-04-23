def test_openapi_schema(client: TestClient):
    response = client.get("/openapi.json")
    assert response.status_code == 200, response.text
    assert response.json() == snapshot(
        {
            "openapi": "3.1.0",
            "info": {"title": "FastAPI", "version": "0.1.0"},
            "paths": {
                "/users/me": {
                    "get": {
                        "responses": {
                            "200": {
                                "description": "Successful Response",
                                "content": {"application/json": {"schema": {}}},
                            }
                        },
                        "summary": "Read Users Me",
                        "operationId": "read_users_me_users_me_get",
                        "security": [{"OAuth2PasswordBearer": []}],
                    }
                }
            },
            "components": {
                "securitySchemes": {
                    "OAuth2PasswordBearer": {
                        "type": "oauth2",
                        "flows": {"password": {"scopes": {}, "tokenUrl": "token"}},
                    }
                },
            },
        }
    )