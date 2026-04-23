async def test_password_auth_single_plant(
    hass: HomeAssistant, mock_growatt_classic_api, mock_setup_entry
) -> None:
    """Test password authentication with single plant."""
    # Repatch plant_list with full plant data for config flow
    mock_growatt_classic_api.plant_list.return_value = GROWATT_PLANT_LIST_RESPONSE

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

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_USERNAME] == FIXTURE_USER_INPUT_PASSWORD[CONF_USERNAME]
    assert result["data"][CONF_PASSWORD] == FIXTURE_USER_INPUT_PASSWORD[CONF_PASSWORD]
    assert result["data"][CONF_PLANT_ID] == "123456"
    assert result["data"][CONF_AUTH_TYPE] == AUTH_PASSWORD
    assert result["data"][CONF_NAME] == "Plant name"
    assert result["result"].unique_id == "123456"