def test_cfg_init():
    """Test configuration initialization utilities from the 'ultralytics.cfg' module."""
    from ultralytics.cfg import check_dict_alignment, copy_default_cfg, smart_value

    with contextlib.suppress(SyntaxError):
        check_dict_alignment({"a": 1}, {"b": 2})
    copy_default_cfg()
    (Path.cwd() / DEFAULT_CFG_PATH.name.replace(".yaml", "_copy.yaml")).unlink(missing_ok=False)

    # Test smart_value() with comprehensive cases
    # Test None conversion
    assert smart_value("none") is None
    assert smart_value("None") is None
    assert smart_value("NONE") is None

    # Test boolean conversion
    assert smart_value("true") is True
    assert smart_value("True") is True
    assert smart_value("TRUE") is True
    assert smart_value("false") is False
    assert smart_value("False") is False
    assert smart_value("FALSE") is False

    # Test numeric conversion (ast.literal_eval)
    assert smart_value("42") == 42
    assert smart_value("-42") == -42
    assert smart_value("3.14") == 3.14
    assert smart_value("-3.14") == -3.14
    assert smart_value("1e-3") == 0.001

    # Test list/tuple conversion (ast.literal_eval)
    assert smart_value("[1, 2, 3]") == [1, 2, 3]
    assert smart_value("(1, 2, 3)") == (1, 2, 3)
    assert smart_value("[640, 640]") == [640, 640]

    # Test dict conversion (ast.literal_eval)
    assert smart_value("{'a': 1, 'b': 2}") == {"a": 1, "b": 2}

    # Test string fallback (when ast.literal_eval fails)
    assert smart_value("some_string") == "some_string"
    assert smart_value("path/to/file") == "path/to/file"
    assert smart_value("hello world") == "hello world"

    # Test that code injection is prevented (ast.literal_eval safety)
    # These should return strings, not execute code
    assert smart_value("__import__('os').system('ls')") == "__import__('os').system('ls')"
    assert smart_value("eval('1+1')") == "eval('1+1')"
    assert smart_value("exec('x=1')") == "exec('x=1')"