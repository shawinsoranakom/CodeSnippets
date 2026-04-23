def test_convert_param_value_stricter_type_checking(parser):
    """Test stricter type checking in the updated implementation."""
    # Boolean now has stricter validation
    assert parser._convert_param_value("true", "boolean") is True
    assert parser._convert_param_value("false", "boolean") is False
    assert parser._convert_param_value("1", "boolean") is True
    assert parser._convert_param_value("0", "boolean") is False

    # These should return original string (not valid boolean values)
    assert parser._convert_param_value("yes", "boolean") == "yes"
    assert parser._convert_param_value("no", "boolean") == "no"
    assert parser._convert_param_value("TRUE", "boolean") is True
    assert parser._convert_param_value("FALSE", "boolean") is False

    # Integer and float now raise exceptions for invalid values
    assert parser._convert_param_value("123abc", "integer") == "123abc"
    assert parser._convert_param_value("123.45.67", "float") == "123.45.67"

    # JSON parsing is stricter - invalid JSON returns original
    assert parser._convert_param_value("{invalid: json}", "object") == "{invalid: json}"
    assert parser._convert_param_value("[1, 2,", "array") == "[1, 2,"

    # Test multi-type with stricter checking
    # "yes" is not valid boolean, but string would accept it
    assert parser._convert_param_value("yes", ["boolean", "string"]) == "yes"

    # "123abc" is not valid integer or float, but string accepts it
    assert (
        parser._convert_param_value("123abc", ["integer", "float", "string"])
        == "123abc"
    )