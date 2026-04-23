async def test_token_auth_invalid_response(
    hass: HomeAssistant, mock_growatt_v1_api, mock_setup_entry
) -> None:
    """Test token authentication with invalid response format, then recovery."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "token_auth"}
    )

    # Return invalid response format (None instead of dict with 'plants' key)
    mock_growatt_v1_api.plant_list.return_value = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], FIXTURE_USER_INPUT_TOKEN
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "token_auth"
    assert result["errors"] == {"base": ERROR_CANNOT_CONNECT}

    # Test recovery - set normal return value
    mock_growatt_v1_api.plant_list.return_value = GROWATT_V1_PLANT_LIST_RESPONSE

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], FIXTURE_USER_INPUT_TOKEN
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_TOKEN] == FIXTURE_USER_INPUT_TOKEN[CONF_TOKEN]
    assert result["data"][CONF_PLANT_ID] == "123456"
    assert result["data"][CONF_AUTH_TYPE] == AUTH_API_TOKEN