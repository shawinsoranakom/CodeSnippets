def test_basic_type_mapping(json_type: str, expected_type: type) -> None:
    schema = {
        "type": "object",
        "properties": {"field": {"type": json_type}},
        "required": ["field"],
    }
    converter = _JSONSchemaToPydantic()
    Model = converter.json_schema_to_pydantic(schema, f"{json_type.capitalize()}Model")

    assert "field" in Model.__annotations__
    field_type = Model.__annotations__["field"]

    # For array/object/null we check the outer type only
    if json_type == "null":
        assert field_type is type(None)
    elif json_type == "array":
        assert getattr(field_type, "__origin__", None) is list
    elif json_type == "object":
        assert field_type in (dict, Dict) or getattr(field_type, "__origin__", None) in (dict, Dict)

    else:
        assert field_type == expected_type