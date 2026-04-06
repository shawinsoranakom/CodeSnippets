def test_openapi_schema(client: TestClient):
    response = client.get("/openapi.json")
    assert response.status_code == 200, response.text
    assert response.json() == snapshot(
        {
            "openapi": "3.1.0",
            "info": {"title": "FastAPI", "version": "0.1.0"},
            "paths": {
                "/user/": {
                    "post": {
                        "summary": "Create User",
                        "operationId": "create_user_user__post",
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/UserIn"}
                                }
                            },
                            "required": True,
                        },
                        "responses": {
                            "200": {
                                "description": "Successful Response",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/BaseUser"
                                        }
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
                    }
                }
            },
            "components": {
                "schemas": {
                    "BaseUser": {
                        "title": "BaseUser",
                        "required": ["username", "email"],
                        "type": "object",
                        "properties": {
                            "username": {"title": "Username", "type": "string"},
                            "email": {
                                "title": "Email",
                                "type": "string",
                                "format": "email",
                            },
                            "full_name": {
                                "title": "Full Name",
                                "anyOf": [{"type": "string"}, {"type": "null"}],
                            },
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
                    "UserIn": {
                        "title": "UserIn",
                        "required": ["username", "email", "password"],
                        "type": "object",
                        "properties": {
                            "username": {"title": "Username", "type": "string"},
                            "email": {
                                "title": "Email",
                                "type": "string",
                                "format": "email",
                            },
                            "full_name": {
                                "title": "Full Name",
                                "anyOf": [{"type": "string"}, {"type": "null"}],
                            },
                            "password": {"title": "Password", "type": "string"},
                        },
                    },
                    "ValidationError": {
                        "title": "ValidationError",
                        "required": ["loc", "msg", "type"],
                        "type": "object",
                        "properties": {
                            "ctx": {"title": "Context", "type": "object"},
                            "input": {"title": "Input"},
                            "loc": {
                                "title": "Location",
                                "type": "array",
                                "items": {
                                    "anyOf": [{"type": "string"}, {"type": "integer"}]
                                },
                            },
                            "msg": {"title": "Message", "type": "string"},
                            "type": {"title": "Error Type", "type": "string"},
                        },
                    },
                }
            },
        }
    )