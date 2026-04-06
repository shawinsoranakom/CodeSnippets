def test_list_alias_schema(path: str):
    openapi = app.openapi()
    body_model_name = get_body_model_name(openapi, path)

    assert app.openapi()["components"]["schemas"][body_model_name] == {
        "properties": {
            "p_alias": {
                "type": "array",
                "items": {
                    "type": "string",
                    "contentMediaType": "application/octet-stream",
                },
                "title": "P Alias",
            },
        },
        "required": ["p_alias"],
        "title": body_model_name,
        "type": "object",
    }