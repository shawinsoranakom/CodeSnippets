async def test_password_auth_invalid_response(
    hass: HomeAssistant, mock_growatt_classic_api, mock_setup_entry
) -> None:
    """Test password authentication with invalid response format, then recovery."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # Select password authentication
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "password_auth"}
    )

    # Simulate invalid response error on first attempt
    mock_growatt_classic_api.login.side_effect = ValueError("Invalid JSON response")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], FIXTURE_USER_INPUT_PASSWORD
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "password_auth"
    assert result["errors"] == {"base": ERROR_CANNOT_CONNECT}

    # Test recovery - reset side_effect and set normal return values
    mock_growatt_classic_api.login.side_effect = None
    mock_growatt_classic_api.login.return_value = GROWATT_LOGIN_RESPONSE
    mock_growatt_classic_api.plant_list.return_value = GROWATT_PLANT_LIST_RESPONSE

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], FIXTURE_USER_INPUT_PASSWORD
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_USERNAME] == FIXTURE_USER_INPUT_PASSWORD[CONF_USERNAME]
    assert result["data"][CONF_PASSWORD] == FIXTURE_USER_INPUT_PASSWORD[CONF_PASSWORD]
    assert result["data"][CONF_PLANT_ID] == "123456"
    assert result["data"][CONF_AUTH_TYPE] == AUTH_PASSWORD