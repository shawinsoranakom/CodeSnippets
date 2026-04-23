def test_required_list_str_alias_schema(path: str):
    openapi = app.openapi()
    body_model_name = get_body_model_name(openapi, path)

    assert app.openapi()["components"]["schemas"][body_model_name] == {
        "properties": {
            "p_alias": {
                "items": {"type": "string"},
                "title": "P Alias",
                "type": "array",
            },
        },
        "required": ["p_alias"],
        "title": body_model_name,
        "type": "object",
    }