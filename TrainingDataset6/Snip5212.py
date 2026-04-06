def test_openapi_schema(mod: ModuleType):
    client = TestClient(mod.app)
    response = client.get("/openapi.json")
    assert response.status_code == 200, response.text
    assert response.json() == snapshot(
        {
            "openapi": "3.1.0",
            "info": {"title": "FastAPI", "version": "0.1.0"},
            "paths": {
                "/token": {
                    "post": {
                        "responses": {
                            "200": {
                                "description": "Successful Response",
                                "content": {
                                    "application/json": {
                                        "schema": {"$ref": "#/components/schemas/Token"}
                                    }
                                },
                            },
                            "422": {
                                "description": "Validation Error",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/HTTPValidationError"
                                        }
                                    }
                                },
                            },
                        },
                        "summary": "Login For Access Token",
                        "operationId": "login_for_access_token_token_post",
                        "requestBody": {
                            "content": {
                                "application/x-www-form-urlencoded": {
                                    "schema": {
                                        "$ref": "#/components/schemas/Body_login_for_access_token_token_post"
                                    }
                                }
                            },
                            "required": True,
                        },
                    }
                },
                "/users/me/": {
                    "get": {
                        "responses": {
                            "200": {
                                "description": "Successful Response",
                                "content": {
                                    "application/json": {
                                        "schema": {"$ref": "#/components/schemas/User"}
                                    }
                                },
                            }
                        },
                        "summary": "Read Users Me",
                        "operationId": "read_users_me_users_me__get",
                        "security": [{"OAuth2PasswordBearer": []}],
                    }
                },
                "/users/me/items/": {
                    "get": {
                        "responses": {
                            "200": {
                                "description": "Successful Response",
                                "content": {"application/json": {"schema": {}}},
                            }
                        },
                        "summary": "Read Own Items",
                        "operationId": "read_own_items_users_me_items__get",
                        "security": [{"OAuth2PasswordBearer": []}],
                    }
                },
            },
            "components": {
                "schemas": {
                    "User": {
                        "title": "User",
                        "required": ["username"],
                        "type": "object",
                        "properties": {
                            "username": {"title": "Username", "type": "string"},
                            "email": {
                                "title": "Email",
                                "anyOf": [{"type": "string"}, {"type": "null"}],
                            },
                            "full_name": {
                                "title": "Full Name",
                                "anyOf": [{"type": "string"}, {"type": "null"}],
                            },
                            "disabled": {
                                "title": "Disabled",
                                "anyOf": [{"type": "boolean"}, {"type": "null"}],
                            },
                        },
                    },
                    "Token": {
                        "title": "Token",
                        "required": ["access_token", "token_type"],
                        "type": "object",
                        "properties": {
                            "access_token": {"title": "Access Token", "type": "string"},
                            "token_type": {"title": "Token Type", "type": "string"},
                        },
                    },
                    "Body_login_for_access_token_token_post": {
                        "title": "Body_login_for_access_token_token_post",
                        "required": ["username", "password"],
                        "type": "object",
                        "properties": {
                            "grant_type": {
                                "title": "Grant Type",
                                "anyOf": [
                                    {"pattern": "^password$", "type": "string"},
                                    {"type": "null"},
                                ],
                            },
                            "username": {"title": "Username", "type": "string"},
                            "password": {
                                "title": "Password",
                                "type": "string",
                                "format": "password",
                            },
                            "scope": {
                                "title": "Scope",
                                "type": "string",
                                "default": "",
                            },
                            "client_id": {
                                "title": "Client Id",
                                "anyOf": [{"type": "string"}, {"type": "null"}],
                            },
                            "client_secret": {
                                "title": "Client Secret",
                                "anyOf": [{"type": "string"}, {"type": "null"}],
                                "format": "password",
                            },
                        },
                    },
                    "ValidationError": {
                        "title": "ValidationError",
                        "required": ["loc", "msg", "type"],
                        "type": "object",
                        "properties": {
                            "loc": {
                                "title": "Location",
                                "type": "array",
                                "items": {
                                    "anyOf": [{"type": "string"}, {"type": "integer"}]
                                },
                            },
                            "msg": {"title": "Message", "type": "string"},
                            "type": {"title": "Error Type", "type": "string"},
                            "input": {"title": "Input"},
                            "ctx": {"title": "Context", "type": "object"},
                        },
                    },
                    "HTTPValidationError": {
                        "title": "HTTPValidationError",
                        "type": "object",
                        "properties": {
                            "detail": {
                                "title": "Detail",
                                "type": "array",
                                "items": {
                                    "$ref": "#/components/schemas/ValidationError"
                                },
                            }
                        },
                    },
                },
                "securitySchemes": {
                    "OAuth2PasswordBearer": {
                        "type": "oauth2",
                        "flows": {
                            "password": {
                                "scopes": {},
                                "tokenUrl": "token",
                            }
                        },
                    }
                },
            },
        }
    )