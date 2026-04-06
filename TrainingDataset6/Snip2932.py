def test_allowed_schema_type(
    type_value: SchemaType | list[SchemaType] | None,
) -> None:
    """Test that Schema accepts SchemaType, List[SchemaType] and None for type field."""
    schema = Schema(type=type_value)
    assert schema.type == type_value