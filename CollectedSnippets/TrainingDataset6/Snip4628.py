def test_openapi_schema(client: TestClient, mod_name: str):
    if mod_name.startswith("tutorial003"):
        response_content = {"application/json": {"schema": {}}}
    else:
        response_content = {"text/html": {"schema": {"type": "string"}}}

    response = client.get("/openapi.json")
    assert response.status_code == 200, response.text
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
                                "content": Is(response_content),
                            }
                        },
                        "summary": "Read Items",
                        "operationId": "read_items_items__get",
                    }
                }
            },
        }
    )