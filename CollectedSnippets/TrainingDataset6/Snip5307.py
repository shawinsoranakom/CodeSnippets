def test_openapi_schema(client: TestClient):
    response = client.get("/openapi.json")
    assert response.status_code == 200, response.text
    assert response.json() == snapshot(
        {
            "openapi": "3.1.0",
            "info": {"title": "FastAPI", "version": "0.1.0"},
            "paths": {
                "/image/stream": {
                    "get": {
                        "summary": "Stream Image",
                        "operationId": "stream_image_image_stream_get",
                        "responses": {
                            "200": {
                                "description": "Successful Response",
                                "content": {
                                    "image/png": {"schema": {"type": "string"}}
                                },
                            }
                        },
                    }
                },
                "/image/stream-no-async": {
                    "get": {
                        "summary": "Stream Image No Async",
                        "operationId": "stream_image_no_async_image_stream_no_async_get",
                        "responses": {
                            "200": {
                                "description": "Successful Response",
                                "content": {
                                    "image/png": {"schema": {"type": "string"}}
                                },
                            }
                        },
                    }
                },
                "/image/stream-no-async-yield-from": {
                    "get": {
                        "summary": "Stream Image No Async Yield From",
                        "operationId": "stream_image_no_async_yield_from_image_stream_no_async_yield_from_get",
                        "responses": {
                            "200": {
                                "description": "Successful Response",
                                "content": {
                                    "image/png": {"schema": {"type": "string"}}
                                },
                            }
                        },
                    }
                },
                "/image/stream-no-annotation": {
                    "get": {
                        "summary": "Stream Image No Annotation",
                        "operationId": "stream_image_no_annotation_image_stream_no_annotation_get",
                        "responses": {
                            "200": {
                                "description": "Successful Response",
                                "content": {
                                    "image/png": {"schema": {"type": "string"}}
                                },
                            }
                        },
                    }
                },
                "/image/stream-no-async-no-annotation": {
                    "get": {
                        "summary": "Stream Image No Async No Annotation",
                        "operationId": "stream_image_no_async_no_annotation_image_stream_no_async_no_annotation_get",
                        "responses": {
                            "200": {
                                "description": "Successful Response",
                                "content": {
                                    "image/png": {"schema": {"type": "string"}}
                                },
                            }
                        },
                    }
                },
            },
        }
    )