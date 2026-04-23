def test_openapi_schema(client: TestClient) -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200, response.text
    assert response.json() == snapshot(
        {
            "openapi": "3.1.0",
            "info": {"title": "FastAPI", "version": "0.1.0"},
            "paths": {
                "/pet/assignment": {
                    "post": {
                        "summary": "Create Pet Assignment",
                        "operationId": "create_pet_assignment_pet_assignment_post",
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "anyOf": [
                                            {"$ref": "#/components/schemas/Cat"},
                                            {"$ref": "#/components/schemas/Dog"},
                                        ],
                                        "title": "Pet",
                                    }
                                }
                            },
                            "required": True,
                        },
                        "responses": {
                            "200": {
                                "description": "Successful Response",
                                "content": {"application/json": {"schema": {}}},
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
                },
                "/pet/annotated": {
                    "post": {
                        "summary": "Create Pet Annotated",
                        "operationId": "create_pet_annotated_pet_annotated_post",
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "oneOf": [
                                            {"$ref": "#/components/schemas/Cat"},
                                            {"$ref": "#/components/schemas/Dog"},
                                        ],
                                        "title": "Pet",
                                    }
                                }
                            },
                            "required": True,
                        },
                        "responses": {
                            "200": {
                                "description": "Successful Response",
                                "content": {"application/json": {"schema": {}}},
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
                },
            },
            "components": {
                "schemas": {
                    "Cat": {
                        "properties": {
                            "pet_type": {
                                "type": "string",
                                "title": "Pet Type",
                                "default": "cat",
                            },
                            "meows": {"type": "integer", "title": "Meows"},
                        },
                        "type": "object",
                        "required": ["meows"],
                        "title": "Cat",
                    },
                    "Dog": {
                        "properties": {
                            "pet_type": {
                                "type": "string",
                                "title": "Pet Type",
                                "default": "dog",
                            },
                            "barks": {"type": "number", "title": "Barks"},
                        },
                        "type": "object",
                        "required": ["barks"],
                        "title": "Dog",
                    },
                    "HTTPValidationError": {
                        "properties": {
                            "detail": {
                                "items": {
                                    "$ref": "#/components/schemas/ValidationError"
                                },
                                "type": "array",
                                "title": "Detail",
                            }
                        },
                        "type": "object",
                        "title": "HTTPValidationError",
                    },
                    "ValidationError": {
                        "properties": {
                            "ctx": {"title": "Context", "type": "object"},
                            "input": {"title": "Input"},
                            "loc": {
                                "items": {
                                    "anyOf": [{"type": "string"}, {"type": "integer"}]
                                },
                                "type": "array",
                                "title": "Location",
                            },
                            "msg": {"type": "string", "title": "Message"},
                            "type": {"type": "string", "title": "Error Type"},
                        },
                        "type": "object",
                        "required": ["loc", "msg", "type"],
                        "title": "ValidationError",
                    },
                }
            },
        }
    )