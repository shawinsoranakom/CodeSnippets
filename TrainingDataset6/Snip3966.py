def test_openapi_schema(client: TestClient):
    response = client.get("openapi.json")
    assert response.json() == snapshot(
        {
            "openapi": "3.1.0",
            "info": {"title": "FastAPI", "version": "0.1.0"},
            "paths": {
                "/users": {
                    "get": {
                        "summary": "Get User",
                        "operationId": "get_user_users_get",
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
                    }
                }
            },
            "components": {
                "schemas": IsOneOf(
                    # Pydantic >= 2.11: no top-level OtherRole
                    {
                        "PlatformRole": {
                            "type": "string",
                            "enum": ["admin", "user"],
                            "title": "PlatformRole",
                        },
                        "User": {
                            "properties": {
                                "username": {"type": "string", "title": "Username"},
                                "role": {
                                    "anyOf": [
                                        {"$ref": "#/components/schemas/PlatformRole"},
                                        {"enum": [], "title": "OtherRole"},
                                    ],
                                    "title": "Role",
                                },
                            },
                            "type": "object",
                            "required": ["username", "role"],
                            "title": "User",
                        },
                    },
                    # Pydantic < 2.11: adds a top-level OtherRole schema
                    {
                        "OtherRole": {
                            "enum": [],
                            "title": "OtherRole",
                        },
                        "PlatformRole": {
                            "type": "string",
                            "enum": ["admin", "user"],
                            "title": "PlatformRole",
                        },
                        "User": {
                            "properties": {
                                "username": {"type": "string", "title": "Username"},
                                "role": {
                                    "anyOf": [
                                        {"$ref": "#/components/schemas/PlatformRole"},
                                        {"enum": [], "title": "OtherRole"},
                                    ],
                                    "title": "Role",
                                },
                            },
                            "type": "object",
                            "required": ["username", "role"],
                            "title": "User",
                        },
                    },
                )
            },
        }
    )