def test_deprecated_with_replacement_key_and_default(
    caplog: pytest.LogCaptureFixture, schema
) -> None:
    """Test deprecation with a replacement key and default.

    Expected behavior:
        - Outputs the appropriate deprecation warning if key is detected
        - Processes schema moving the value from key to replacement_key
        - Processes schema changing nothing if only replacement_key provided
        - No warning if only replacement_key provided
        - No warning if neither key nor replacement_key are provided
            - Adds replacement_key with default value in this case
    """
    deprecated_schema = vol.All(
        cv.deprecated("mars", replacement_key="jupiter", default=False), schema
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
    assert output == {"venus": True, "jupiter": False}

    deprecated_schema_with_default = vol.All(
        vol.Schema(
            {
                "venus": cv.boolean,
                vol.Optional("mars", default=False): cv.boolean,
                vol.Optional("jupiter", default=False): cv.boolean,
            }
        ),
        cv.deprecated("mars", replacement_key="jupiter", default=False),
    )

    test_data = {"mars": True}
    output = deprecated_schema_with_default(test_data.copy())
    assert len(caplog.records) == 1
    assert (
        "The 'mars' option is deprecated, please replace it with 'jupiter'"
    ) in caplog.text
    assert output == {"jupiter": True}