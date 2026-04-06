def test_openapi_schema():
    response = client.get("/openapi.json")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == snapshot(
        {
            "components": {
                "schemas": {
                    "HTTPValidationError": {
                        "properties": {
                            "detail": {
                                "items": {
                                    "$ref": "#/components/schemas/ValidationError"
                                },
                                "title": "Detail",
                                "type": "array",
                            }
                        },
                        "title": "HTTPValidationError",
                        "type": "object",
                    },
                    "ValidationError": {
                        "properties": {
                            "ctx": {"title": "Context", "type": "object"},
                            "input": {"title": "Input"},
                            "loc": {
                                "items": {
                                    "anyOf": [{"type": "string"}, {"type": "integer"}]
                                },
                                "title": "Location",
                                "type": "array",
                            },
                            "msg": {"title": "Message", "type": "string"},
                            "type": {"title": "Error Type", "type": "string"},
                        },
                        "required": ["loc", "msg", "type"],
                        "title": "ValidationError",
                        "type": "object",
                    },
                }
            },
            "info": {"title": "FastAPI", "version": "0.1.0"},
            "openapi": "3.1.0",
            "paths": {
                "/{repeated_alias}": {
                    "get": {
                        "operationId": "get_parameters_with_repeated_aliases__repeated_alias__get",
                        "parameters": [
                            {
                                "in": "path",
                                "name": "repeated_alias",
                                "required": True,
                                "schema": {"title": "Repeated Alias", "type": "string"},
                            },
                            {
                                "in": "query",
                                "name": "repeated_alias",
                                "required": True,
                                "schema": {"title": "Repeated Alias", "type": "string"},
                            },
                        ],
                        "responses": {
                            "200": {
                                "content": {"application/json": {"schema": {}}},
                                "description": "Successful Response",
                            },
                            "422": {
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/HTTPValidationError"
                                        }
                                    }
                                },
                                "description": "Validation Error",
                            },
                        },
                        "summary": "Get Parameters With Repeated Aliases",
                    }
                }
            },
        }
    )