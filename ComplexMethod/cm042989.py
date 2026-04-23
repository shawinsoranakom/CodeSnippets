def _validate_schema(schema: dict):
    """Validate that a generated schema has the expected structure."""
    assert isinstance(schema, dict), f"Schema must be a dict, got {type(schema)}"
    assert "name" in schema, "Schema must have a 'name' field"
    assert "baseSelector" in schema, "Schema must have a 'baseSelector' field"
    assert "fields" in schema, "Schema must have a 'fields' field"
    assert isinstance(schema["fields"], list), "'fields' must be a list"
    assert len(schema["fields"]) > 0, "'fields' must not be empty"
    for field in schema["fields"]:
        assert "name" in field, f"Each field must have a 'name': {field}"
        assert "selector" in field, f"Each field must have a 'selector': {field}"
        assert "type" in field, f"Each field must have a 'type': {field}"