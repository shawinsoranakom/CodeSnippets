def test_convert_param_value_checked_helper(parser):
    """Test the _convert_param_value_checked helper function indirectly."""
    # This tests the behavior through the main function
    # Valid conversions should work
    assert parser._convert_param_value("123", "integer") == 123
    assert parser._convert_param_value("123.45", "float") == 123.45
    assert parser._convert_param_value("true", "boolean") is True
    assert parser._convert_param_value('{"x": 1}', "object") == {"x": 1}

    # Invalid conversions should return original value (exception caught)
    assert parser._convert_param_value("abc", "integer") == "abc"
    assert parser._convert_param_value("abc", "float") == "abc"
    assert parser._convert_param_value("yes", "boolean") == "yes"
    assert parser._convert_param_value("{invalid}", "object") == "{invalid}"

    # Test that null handling works in checked function
    assert parser._convert_param_value("null", "integer") is None
    assert parser._convert_param_value("null", "boolean") is None
    assert parser._convert_param_value("null", "object") is None