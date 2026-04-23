def test_openapi_schema():
    response = client.get("/openapi.json")
    assert response.status_code == status.HTTP_200_OK
    actual_schema = response.json()
    assert (
        len(actual_schema["paths"]["/"]["get"]["parameters"]) == 1
    )  # primary goal of this test
    assert actual_schema == snapshot(
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
                "/": {
                    "get": {
                        "operationId": "get_deps__get",
                        "parameters": [
                            {
                                "in": "header",
                                "name": "someheader",
                                "required": True,
                                "schema": {"title": "Someheader", "type": "string"},
                            }
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
                        "summary": "Get Deps",
                    }
                }
            },
        }
    )