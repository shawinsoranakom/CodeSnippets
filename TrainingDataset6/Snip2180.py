def test_serialize_sequence_value_with_none_first_in_union():
    """Test that serialize_sequence_value handles Union[None, List[...]] correctly."""
    from typing import Union

    from fastapi._compat import v2

    # Use Union[None, list[str]] to ensure None comes first in the union args
    field_info = FieldInfo(annotation=Union[None, list[str]])  # noqa: UP007
    field = v2.ModelField(name="items", field_info=field_info)
    result = v2.serialize_sequence_value(field=field, value=["x", "y"])
    assert result == ["x", "y"]
    assert isinstance(result, list)