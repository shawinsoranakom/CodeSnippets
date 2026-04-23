async def test_password_auth_multiple_plants(
    hass: HomeAssistant, mock_growatt_classic_api, mock_setup_entry
) -> None:
    """Test password authentication with multiple plants."""
    # Repatch plant_list with multiple plants
    plant_list = deepcopy(GROWATT_PLANT_LIST_RESPONSE)
    plant_list["data"].append(
        {
            "plantMoneyText": "300.0 (€)",
            "plantName": "Plant name 2",
            "plantId": "789012",
            "isHaveStorage": "true",
            "todayEnergy": "1.5 kWh",
            "totalEnergy": "1.8 MWh",
            "currentPower": "420.0 W",
        }
    )
    mock_growatt_classic_api.plant_list.return_value = plant_list

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

    # Should show plant selection form
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "plant"

    # Select first plant
    user_input = {CONF_PLANT_ID: "123456"}
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_USERNAME] == FIXTURE_USER_INPUT_PASSWORD[CONF_USERNAME]
    assert result["data"][CONF_PASSWORD] == FIXTURE_USER_INPUT_PASSWORD[CONF_PASSWORD]
    assert result["data"][CONF_PLANT_ID] == "123456"
    assert result["data"][CONF_AUTH_TYPE] == AUTH_PASSWORD
    assert result["result"].unique_id == "123456"