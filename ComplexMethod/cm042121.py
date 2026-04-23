def test_parse_python_code():
    expected_result = "print('Hello, world!')"
    assert OutputParser.parse_python_code("```python\nprint('Hello, world!')```") == expected_result
    assert OutputParser.parse_python_code("```python\nprint('Hello, world!')") == expected_result
    assert OutputParser.parse_python_code("print('Hello, world!')") == expected_result
    assert OutputParser.parse_python_code("print('Hello, world!')```") == expected_result
    assert OutputParser.parse_python_code("print('Hello, world!')```") == expected_result
    expected_result = "print('```Hello, world!```')"
    assert OutputParser.parse_python_code("```python\nprint('```Hello, world!```')```") == expected_result
    assert OutputParser.parse_python_code("The code is: ```python\nprint('```Hello, world!```')```") == expected_result
    assert OutputParser.parse_python_code("xxx.\n```python\nprint('```Hello, world!```')```\nxxx") == expected_result

    with pytest.raises(ValueError):
        OutputParser.parse_python_code("xxx =")