def test_list_schema(path: str):
    openapi = app.openapi()
    body_model_name = get_body_model_name(openapi, path)

    assert app.openapi()["components"]["schemas"][body_model_name] == {
        "properties": {
            "p": {
                "type": "array",
                "items": {
                    "type": "string",
                    "contentMediaType": "application/octet-stream",
                },
                "title": "P",
            },
        },
        "required": ["p"],
        "title": body_model_name,
        "type": "object",
    }