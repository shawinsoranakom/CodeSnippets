def test_openapi():
    response = client.get("/openapi.json")
    assert response.status_code == 200, response.text
    openapi_schema = response.json()

    assert openapi_schema["components"]["schemas"]["MyModel"]["description"] == (
        "A model with a form feed character in the title.\n"
    )