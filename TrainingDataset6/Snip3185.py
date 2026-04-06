def test_required_list_validation_alias_schema(path: str):
    openapi = app.openapi()
    body_model_name = get_body_model_name(openapi, path)

    assert app.openapi()["components"]["schemas"][body_model_name] == {
        "properties": {
            "p_val_alias": {
                "items": {"type": "string"},
                "title": "P Val Alias",
                "type": "array",
            },
        },
        "required": ["p_val_alias"],
        "title": body_model_name,
        "type": "object",
    }