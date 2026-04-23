def test_deprecated_with_default(caplog: pytest.LogCaptureFixture, schema) -> None:
    """Test deprecation behaves correctly with a default value.

    This is likely a scenario that would never occur.

    Expected behavior:
        - Behaves identically as when the default value was not present
    """
    deprecated_schema = vol.All(cv.deprecated("mars", default=False), schema)

    test_data = {"mars": True}
    with patch(
        "homeassistant.helpers.config_validation.get_integration_logger",
        return_value=logging.getLogger(__name__),
    ):
        output = deprecated_schema(test_data.copy())
    assert len(caplog.records) == 1
    assert caplog.records[0].name == __name__
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