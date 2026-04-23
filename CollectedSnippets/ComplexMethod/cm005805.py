def test_template_field_defaults(sample_template_field: Input):
    assert sample_template_field.field_type == "str"
    assert sample_template_field.required is False
    assert sample_template_field.placeholder == ""
    assert sample_template_field.is_list is False
    assert sample_template_field.show is True
    assert sample_template_field.multiline is False
    assert sample_template_field.value is None
    assert sample_template_field.file_types == []
    assert sample_template_field.file_path == ""
    assert sample_template_field.name == "test_field"
    assert sample_template_field.password is None