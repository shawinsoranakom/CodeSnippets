def test_deprecated_or_removed_param_and_raise(
    caplog: pytest.LogCaptureFixture, schema
) -> None:
    """Test removed or deprecation options and fail the config validation by raising an exception.

    Expected behavior:
        - Outputs the appropriate deprecation or removed from support error if key is detected
    """
    removed_schema = vol.All(cv.deprecated("mars", raise_if_present=True), schema)

    test_data = {"mars": True}
    with pytest.raises(vol.Invalid) as excinfo:
        removed_schema(test_data)
    assert (
        "The 'mars' option is deprecated, please remove it from your configuration"
        in str(excinfo.value)
    )
    assert len(caplog.records) == 0

    test_data = {"venus": True}
    output = removed_schema(test_data.copy())
    assert len(caplog.records) == 0
    assert test_data == output

    deprecated_schema = vol.All(cv.removed("mars"), schema)

    test_data = {"mars": True}
    with pytest.raises(vol.Invalid) as excinfo:
        deprecated_schema(test_data)
    assert (
        "The 'mars' option has been removed, please remove it from your configuration"
        in str(excinfo.value)
    )
    assert len(caplog.records) == 0

    test_data = {"venus": True}
    output = deprecated_schema(test_data.copy())
    assert len(caplog.records) == 0
    assert test_data == output