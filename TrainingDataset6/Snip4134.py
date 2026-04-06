def test_openapi_schema():
    response = client.get("/openapi.json")
    assert response.status_code == 200, response.text
    assert response.json() == snapshot(
        {
            "openapi": "3.1.0",
            "info": {"title": "FastAPI", "version": "0.1.0"},
            "paths": {
                "/admin": {
                    "get": {
                        "summary": "Read Admin",
                        "operationId": "read_admin_admin_get",
                        "responses": {
                            "200": {
                                "description": "Successful Response",
                                "content": {"application/json": {"schema": {}}},
                            }
                        },
                        "security": [
                            {"OAuth2AuthorizationCodeBearer": ["read", "write"]}
                        ],
                    }
                }
            },
            "components": {
                "securitySchemes": {
                    "OAuth2AuthorizationCodeBearer": {
                        "type": "oauth2",
                        "flows": {
                            "authorizationCode": {
                                "scopes": {
                                    "read": "Read access",
                                    "write": "Write access",
                                },
                                "authorizationUrl": "api/oauth/authorize",
                                "tokenUrl": "/api/oauth/token",
                            }
                        },
                    }
                }
            },
        }
    )