def test_serialize_sequence_value_with_optional_list():
    """Test that serialize_sequence_value handles optional lists correctly."""
    from fastapi._compat import v2

    field_info = FieldInfo(annotation=list[str] | None)
    field = v2.ModelField(name="items", field_info=field_info)
    result = v2.serialize_sequence_value(field=field, value=["a", "b", "c"])
    assert result == ["a", "b", "c"]
    assert isinstance(result, list)