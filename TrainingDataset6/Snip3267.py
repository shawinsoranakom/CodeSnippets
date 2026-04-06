def test_required_str_alias_schema(path: str):
    openapi = app.openapi()
    body_model_name = get_body_model_name(openapi, path)

    assert app.openapi()["components"]["schemas"][body_model_name] == {
        "properties": {
            "p_alias": {"title": "P Alias", "type": "string"},
        },
        "required": ["p_alias"],
        "title": body_model_name,
        "type": "object",
    }