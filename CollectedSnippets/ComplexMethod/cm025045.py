def test_deprecated_or_removed_logger_with_config_attributes(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test if the logger outputs the correct message if the line and file attribute is available in config."""
    file: str = "configuration.yaml"
    line: int = 54

    # test as deprecated option
    replacement_key = "jupiter"
    option_status = "is deprecated"
    replacement = f"'mars' option near {file}:{line} {option_status}, please replace it with '{replacement_key}'"
    config = OrderedDict([("mars", "blah")])
    setattr(config, "__config_file__", file)
    setattr(config, "__line__", line)

    validated = cv.deprecated("mars", replacement_key=replacement_key, default=False)(
        config
    )
    assert "mars" not in validated  # Removed because a replacement_key is defined

    assert len(caplog.records) == 1
    assert replacement in caplog.text

    caplog.clear()
    assert len(caplog.records) == 0

    # test as removed option
    option_status = "has been removed"
    replacement = f"'mars' option near {file}:{line} {option_status}, please remove it from your configuration"
    config = OrderedDict([("mars", "blah")])
    setattr(config, "__config_file__", file)
    setattr(config, "__line__", line)

    validated = cv.removed("mars", default=False, raise_if_present=False)(config)
    assert "mars" not in validated  # Removed because by cv.removed

    assert len(caplog.records) == 1
    assert replacement in caplog.text

    caplog.clear()
    assert len(caplog.records) == 0