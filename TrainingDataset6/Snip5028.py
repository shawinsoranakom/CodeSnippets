def test_openapi_schema(client: TestClient):
    response = client.get("/openapi.json")
    assert response.status_code == 200, response.text

    parameters_schema = {
        "anyOf": [
            {
                "type": "string",
                "minLength": 3,
                "maxLength": 50,
                "pattern": "^fixedquery$",
            },
            {"type": "null"},
        ],
        "title": "Query string",
        "description": "Query string for the items to search in the database that have a good match",
        # See https://github.com/pydantic/pydantic/blob/80353c29a824c55dea4667b328ba8f329879ac9f/tests/test_fastapi.sh#L25-L34.
        **({"deprecated": True} if PYDANTIC_VERSION_MINOR_TUPLE >= (2, 10) else {}),
    }

    assert response.json() == snapshot(
        {
            "openapi": "3.1.0",
            "info": {"title": "FastAPI", "version": "0.1.0"},
            "paths": {
                "/items/": {
                    "get": {
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
                        "summary": "Read Items",
                        "operationId": "read_items_items__get",
                        "parameters": [
                            {
                                "description": "Query string for the items to search in the database that have a good match",
                                "required": False,
                                "deprecated": True,
                                "schema": Is(parameters_schema),
                                "name": "item-query",
                                "in": "query",
                            }
                        ],
                    }
                }
            },
            "components": {
                "schemas": {
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
                }
            },
        }
    )