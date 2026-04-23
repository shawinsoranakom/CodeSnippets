async def test_password_auth_incorrect_login(
    hass: HomeAssistant, mock_growatt_classic_api, mock_setup_entry
) -> None:
    """Test password authentication with incorrect credentials, then recovery."""
    # Simulate incorrect login
    mock_growatt_classic_api.login.return_value = {
        "msg": LOGIN_INVALID_AUTH_CODE,
        "success": False,
    }

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # Select password authentication
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "password_auth"}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], FIXTURE_USER_INPUT_PASSWORD
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "password_auth"
    assert result["errors"] == {"base": ERROR_INVALID_AUTH}

    # Test recovery - repatch for correct credentials
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