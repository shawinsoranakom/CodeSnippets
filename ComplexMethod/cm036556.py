def test_convert_param_value_edge_cases(parser):
    """Test edge cases for _convert_param_value."""
    # Empty string
    assert parser._convert_param_value("", "string") == ""
    assert (
        parser._convert_param_value("", "integer") == ""
    )  # Invalid int returns original

    # Whitespace - trimmed by conversion functions
    assert parser._convert_param_value("  123  ", "integer") == 123
    assert parser._convert_param_value("  true  ", "boolean") is True

    # Numeric strings with special characters
    assert parser._convert_param_value("123.45.67", "float") == "123.45.67"
    assert parser._convert_param_value("123abc", "integer") == "123abc"

    # JSON with whitespace - should parse correctly
    assert parser._convert_param_value('  { "key" : "value" }  ', "object") == {
        "key": "value"
    }

    # Invalid JSON returns original
    assert parser._convert_param_value("{invalid}", "object") == "{invalid}"
    assert parser._convert_param_value("[1, 2,", "array") == "[1, 2,"