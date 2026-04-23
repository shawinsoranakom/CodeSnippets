def test_deprecated_logger_with_one_config_attribute(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test if the logger outputs the correct message if only one of line and file attribute is available in config."""
    file: str = "configuration.yaml"
    line: int = 54
    replacement = f"'mars' option near {file}:{line} is deprecated"
    config = OrderedDict([("mars", "blah")])
    setattr(config, "__config_file__", file)

    cv.deprecated("mars", replacement_key="jupiter", default=False)(config)

    assert len(caplog.records) == 1
    assert replacement not in caplog.text
    assert (
        "The 'mars' option is deprecated, please replace it with 'jupiter'"
    ) in caplog.text

    caplog.clear()
    assert len(caplog.records) == 0

    config = OrderedDict([("mars", "blah")])
    setattr(config, "__line__", line)

    cv.deprecated("mars", replacement_key="jupiter", default=False)(config)

    assert len(caplog.records) == 1
    assert replacement not in caplog.text
    assert (
        "The 'mars' option is deprecated, please replace it with 'jupiter'"
    ) in caplog.text

    caplog.clear()
    assert len(caplog.records) == 0