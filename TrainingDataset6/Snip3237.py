def test_optional_str_alias_schema(path: str):
    openapi = app.openapi()
    body_model_name = get_body_model_name(openapi, path)

    assert app.openapi()["components"]["schemas"][body_model_name] == {
        "properties": {
            "p_alias": {
                "anyOf": [{"type": "string"}, {"type": "null"}],
                "title": "P Alias",
            },
        },
        "title": body_model_name,
        "type": "object",
    }