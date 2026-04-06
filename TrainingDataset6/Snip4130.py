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
                        "summary": "Root",
                        "operationId": "root__get",
                        "responses": {
                            "200": {
                                "description": "Successful Response",
                                "content": {"application/json": {"schema": {}}},
                            }
                        },
                        "security": [{"OAuth2AuthorizationCodeBearer": []}],
                    }
                },
                "/with-oauth2-scheme": {
                    "get": {
                        "summary": "Read With Oauth2 Scheme",
                        "operationId": "read_with_oauth2_scheme_with_oauth2_scheme_get",
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
                },
                "/with-get-token": {
                    "get": {
                        "summary": "Read With Get Token",
                        "operationId": "read_with_get_token_with_get_token_get",
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
                },
                "/items/": {
                    "get": {
                        "summary": "Read Items",
                        "operationId": "read_items_items__get",
                        "responses": {
                            "200": {
                                "description": "Successful Response",
                                "content": {"application/json": {"schema": {}}},
                            }
                        },
                        "security": [
                            {"OAuth2AuthorizationCodeBearer": ["read"]},
                        ],
                    },
                    "post": {
                        "summary": "Create Item",
                        "operationId": "create_item_items__post",
                        "responses": {
                            "200": {
                                "description": "Successful Response",
                                "content": {"application/json": {"schema": {}}},
                            }
                        },
                        "security": [
                            {"OAuth2AuthorizationCodeBearer": ["read", "write"]},
                        ],
                    },
                },
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
                                "authorizationUrl": "authorize",
                                "tokenUrl": "token",
                            }
                        },
                    }
                }
            },
        }
    )