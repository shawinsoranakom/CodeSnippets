def test_openapi(client: TestClient):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert response.json() == snapshot(
        {
            "info": {
                "title": "FastAPI",
                "version": "0.1.0",
            },
            "openapi": "3.1.0",
            "paths": {
                "/graphql": {
                    "get": {
                        "operationId": "handle_http_get_graphql_get",
                        "responses": {
                            "200": {
                                "content": {
                                    "application/json": {
                                        "schema": {},
                                    },
                                },
                                "description": "The GraphiQL integrated development environment.",
                            },
                            "404": {
                                "description": "Not found if GraphiQL or query via GET are not enabled.",
                            },
                        },
                        "summary": "Handle Http Get",
                    },
                    "post": {
                        "operationId": "handle_http_post_graphql_post",
                        "responses": {
                            "200": {
                                "content": {
                                    "application/json": {
                                        "schema": {},
                                    },
                                },
                                "description": "Successful Response",
                            },
                        },
                        "summary": "Handle Http Post",
                    },
                },
            },
        }
    )