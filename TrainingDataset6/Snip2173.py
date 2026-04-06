def test_model_field_default_required():
    from fastapi._compat import v2

    # For coverage
    field_info = FieldInfo(annotation=str)
    field = v2.ModelField(name="foo", field_info=field_info)
    assert field.default is Undefined