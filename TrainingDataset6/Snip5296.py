def test_openapi_schema(client: TestClient):
    response = client.get("/openapi.json")
    assert response.status_code == 200, response.text
    assert response.json() == snapshot(
        {
            "openapi": "3.1.0",
            "info": {"title": "FastAPI", "version": "0.1.0"},
            "paths": {
                "/heroes/": {
                    "post": {
                        "summary": "Create Hero",
                        "operationId": "create_hero_heroes__post",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/HeroCreate"
                                    }
                                }
                            },
                        },
                        "responses": {
                            "200": {
                                "description": "Successful Response",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/HeroPublic"
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
                    },
                    "get": {
                        "summary": "Read Heroes",
                        "operationId": "read_heroes_heroes__get",
                        "parameters": [
                            {
                                "name": "offset",
                                "in": "query",
                                "required": False,
                                "schema": {
                                    "type": "integer",
                                    "default": 0,
                                    "title": "Offset",
                                },
                            },
                            {
                                "name": "limit",
                                "in": "query",
                                "required": False,
                                "schema": {
                                    "type": "integer",
                                    "maximum": 100,
                                    "default": 100,
                                    "title": "Limit",
                                },
                            },
                        ],
                        "responses": {
                            "200": {
                                "description": "Successful Response",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "array",
                                            "items": {
                                                "$ref": "#/components/schemas/HeroPublic"
                                            },
                                            "title": "Response Read Heroes Heroes  Get",
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
                    },
                },
                "/heroes/{hero_id}": {
                    "get": {
                        "summary": "Read Hero",
                        "operationId": "read_hero_heroes__hero_id__get",
                        "parameters": [
                            {
                                "name": "hero_id",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "integer", "title": "Hero Id"},
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "Successful Response",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/HeroPublic"
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
                    },
                    "patch": {
                        "summary": "Update Hero",
                        "operationId": "update_hero_heroes__hero_id__patch",
                        "parameters": [
                            {
                                "name": "hero_id",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "integer", "title": "Hero Id"},
                            }
                        ],
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/HeroUpdate"
                                    }
                                }
                            },
                        },
                        "responses": {
                            "200": {
                                "description": "Successful Response",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/HeroPublic"
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
                    },
                    "delete": {
                        "summary": "Delete Hero",
                        "operationId": "delete_hero_heroes__hero_id__delete",
                        "parameters": [
                            {
                                "name": "hero_id",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "integer", "title": "Hero Id"},
                            }
                        ],
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
                    },
                },
            },
            "components": {
                "schemas": {
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
                    "HeroCreate": {
                        "properties": {
                            "name": {"type": "string", "title": "Name"},
                            "age": {
                                "anyOf": [{"type": "integer"}, {"type": "null"}],
                                "title": "Age",
                            },
                            "secret_name": {"type": "string", "title": "Secret Name"},
                        },
                        "type": "object",
                        "required": ["name", "secret_name"],
                        "title": "HeroCreate",
                    },
                    "HeroPublic": {
                        "properties": {
                            "name": {"type": "string", "title": "Name"},
                            "age": {
                                "anyOf": [{"type": "integer"}, {"type": "null"}],
                                "title": "Age",
                            },
                            "id": {"type": "integer", "title": "Id"},
                        },
                        "type": "object",
                        "required": ["name", "id"],
                        "title": "HeroPublic",
                    },
                    "HeroUpdate": {
                        "properties": {
                            "name": {
                                "anyOf": [{"type": "string"}, {"type": "null"}],
                                "title": "Name",
                            },
                            "age": {
                                "anyOf": [{"type": "integer"}, {"type": "null"}],
                                "title": "Age",
                            },
                            "secret_name": {
                                "anyOf": [{"type": "string"}, {"type": "null"}],
                                "title": "Secret Name",
                            },
                        },
                        "type": "object",
                        "title": "HeroUpdate",
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