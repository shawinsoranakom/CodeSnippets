def test_process_field_parameters_valid(parameter_handler, mock_vertex):
    """Test processing field parameters with a valid mix of field types."""
    new_template = {
        "str_field": {"type": "str", "value": "test", "show": True},
        "int_field": {"type": "int", "value": "123", "show": True, "load_from_db": True},
        "float_field": {"type": "float", "value": "456.78", "show": True},
        "code_field": {"type": "code", "value": "['a', 'b']", "show": True},
        "dict_field": {"type": "dict", "value": {"key": "value"}, "show": True},
        "bool_field": {"type": "bool", "value": True, "show": True},
        "file_field": {"type": "file", "value": None, "file_path": "/flowid/file.txt", "show": True},
        "hidden_field": {"type": "str", "value": "hidden", "show": False},
        "str_list_field": {"type": "str", "value": ["a", "b"], "show": True},
    }
    # Override the vertex template for this test
    mock_vertex.data["node"]["template"] = new_template
    parameter_handler.template_dict = {key: value for key, value in new_template.items() if isinstance(value, dict)}

    params, load_from_db_fields = parameter_handler.process_field_parameters()

    # Validate string field (unescape_string likely returns the same string)
    assert params["str_field"] == unescape_string("test")
    # Validate int_field becomes integer 123 and appears in load_from_db_fields
    assert params["int_field"] == 123
    assert "int_field" in load_from_db_fields
    # Validate float_field becomes float 456.78
    assert params["float_field"] == 456.78
    # Validate code_field becomes evaluated list ['a', 'b']
    assert params["code_field"] == ["a", "b"]
    # Validate dict_field is as provided
    assert params["dict_field"] == {"key": "value"}
    # Validate bool_field remains True
    assert params["bool_field"] is True
    # Validate file_field uses the storage service (mock returns "/mocked/full/path")
    assert params["file_field"] == "/mocked/full/path"
    # Validate hidden field is skipped
    assert "hidden_field" not in params
    # Validate str_list_field has been processed correctly
    assert params["str_list_field"] == [unescape_string("a"), unescape_string("b")]