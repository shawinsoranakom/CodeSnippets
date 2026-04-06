def test_required_schema(path: str):
    openapi = app.openapi()
    body_model_name = get_body_model_name(openapi, path)

    assert app.openapi()["components"]["schemas"][body_model_name] == {
        "properties": {
            "p": {
                "title": "P",
                "type": "string",
                "contentMediaType": "application/octet-stream",
            },
        },
        "required": ["p"],
        "title": body_model_name,
        "type": "object",
    }