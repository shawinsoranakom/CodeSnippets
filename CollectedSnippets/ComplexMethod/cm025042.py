def test_deprecated_with_replacement_key(
    caplog: pytest.LogCaptureFixture, schema
) -> None:
    """Test deprecation behaves correctly when only a replacement key is provided.

    Expected behavior:
        - Outputs the appropriate deprecation warning if key is detected
        - Processes schema moving the value from key to replacement_key
        - Processes schema changing nothing if only replacement_key provided
        - No warning if only replacement_key provided
        - No warning or difference in output if neither key nor
            replacement_key are provided
    """
    deprecated_schema = vol.All(
        cv.deprecated("mars", replacement_key="jupiter"), schema
    )

    test_data = {"mars": True}
    output = deprecated_schema(test_data.copy())
    assert len(caplog.records) == 1
    assert (
        "The 'mars' option is deprecated, please replace it with 'jupiter'"
    ) in caplog.text
    assert output == {"jupiter": True}

    caplog.clear()
    assert len(caplog.records) == 0

    test_data = {"jupiter": True}
    output = deprecated_schema(test_data.copy())
    assert len(caplog.records) == 0
    assert test_data == output

    test_data = {"venus": True}
    output = deprecated_schema(test_data.copy())
    assert len(caplog.records) == 0
    assert test_data == output