def test_deprecated_with_no_optionals(caplog: pytest.LogCaptureFixture, schema) -> None:
    """Test deprecation behaves correctly when optional params are None.

    Expected behavior:
        - Outputs the appropriate deprecation warning if key is detected
        - Processes schema without changing any values
        - No warning or difference in output if key is not provided
    """
    deprecated_schema = vol.All(cv.deprecated("mars"), schema)

    test_data = {"mars": True}
    output = deprecated_schema(test_data.copy())
    assert len(caplog.records) == 1
    assert caplog.records[0].name in [
        __name__,
        "homeassistant.helpers.config_validation",
    ]
    assert (
        "The 'mars' option is deprecated, please remove it from your configuration"
    ) in caplog.text
    assert test_data == output

    caplog.clear()
    assert len(caplog.records) == 0

    test_data = {"venus": True}
    output = deprecated_schema(test_data.copy())
    assert len(caplog.records) == 0
    assert test_data == output