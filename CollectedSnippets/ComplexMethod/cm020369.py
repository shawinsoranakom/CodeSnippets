async def test_token_auth_api_error(
    hass: HomeAssistant,
    mock_growatt_v1_api,
    mock_setup_entry,
    error_code: int,
    expected_error: str,
) -> None:
    """Test token authentication with V1 API error maps to correct error type."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "token_auth"}
    )

    error = growattServer.GrowattV1ApiError("API error")
    error.error_code = error_code
    mock_growatt_v1_api.plant_list.side_effect = error

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], FIXTURE_USER_INPUT_TOKEN
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "token_auth"
    assert result["errors"] == {"base": expected_error}

    # Test recovery
    mock_growatt_v1_api.plant_list.side_effect = None
    mock_growatt_v1_api.plant_list.return_value = GROWATT_V1_PLANT_LIST_RESPONSE

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], FIXTURE_USER_INPUT_TOKEN
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_TOKEN] == FIXTURE_USER_INPUT_TOKEN[CONF_TOKEN]
    assert result["data"][CONF_PLANT_ID] == "123456"
    assert result["data"][CONF_AUTH_TYPE] == AUTH_API_TOKEN