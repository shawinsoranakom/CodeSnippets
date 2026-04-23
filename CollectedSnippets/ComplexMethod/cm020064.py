async def test_config_flow_errors(
    hass: HomeAssistant,
    b2_fixture: BackblazeFixture,
    error_type: str,
    setup: dict,
    expected_error: str,
    expected_field: str,
) -> None:
    """Test various config flow error scenarios."""

    if error_type == "invalid_auth":
        result = await _async_start_flow(hass, setup["key_id"], setup["app_key"])
    elif error_type == "invalid_bucket":
        invalid_input = {**USER_INPUT, "bucket": setup["bucket"]}
        result = await _async_start_flow(
            hass, b2_fixture.key_id, b2_fixture.application_key, invalid_input
        )
    elif "patch" in setup:
        with patch(setup["patch"], side_effect=setup["exception"](*setup["args"])):
            result = await _async_start_flow(
                hass, b2_fixture.key_id, b2_fixture.application_key
            )
    elif "mock_capabilities" in setup:
        with patch(
            "b2sdk.v2.RawSimulator.account_info.get_allowed",
            return_value={"capabilities": setup["mock_capabilities"]},
        ):
            result = await _async_start_flow(
                hass, b2_fixture.key_id, b2_fixture.application_key
            )
    elif "mock_allowed" in setup:
        with patch(
            "b2sdk.v2.RawSimulator.account_info.get_allowed",
            return_value=setup["mock_allowed"],
        ):
            result = await _async_start_flow(
                hass, b2_fixture.key_id, b2_fixture.application_key
            )
    elif "mock_prefix" in setup:
        with patch(
            "b2sdk.v2.RawSimulator.account_info.get_allowed",
            return_value={
                "capabilities": ["writeFiles", "listFiles", "deleteFiles", "readFiles"],
                "namePrefix": setup["mock_prefix"],
            },
        ):
            result = await _async_start_flow(
                hass, b2_fixture.key_id, b2_fixture.application_key
            )

    assert result.get("type") is FlowResultType.FORM
    assert result.get("errors") == {expected_field: expected_error}

    if error_type == "restricted_bucket":
        assert result.get("description_placeholders") == {
            "brand_name": "Backblaze B2",
            "restricted_bucket_name": "testBucket",
        }
    elif error_type == "invalid_prefix":
        assert result.get("description_placeholders") == {
            "brand_name": "Backblaze B2",
            "allowed_prefix": "test/",
        }
    elif error_type == "bad_request":
        assert result.get("description_placeholders") == {
            "brand_name": "Backblaze B2",
            "error_message": "test (bad_request)",
        }