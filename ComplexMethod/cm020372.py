async def test_token_auth_multiple_plants(
    hass: HomeAssistant, mock_growatt_v1_api, mock_setup_entry
) -> None:
    """Test token authentication with multiple plants."""
    # Repatch plant_list with multiple plants
    mock_growatt_v1_api.plant_list.return_value = GROWATT_V1_MULTIPLE_PLANTS_RESPONSE

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # Select token authentication
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "token_auth"}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], FIXTURE_USER_INPUT_TOKEN
    )

    # Should show plant selection form
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "plant"

    # Select second plant
    user_input = {CONF_PLANT_ID: "789012"}
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_TOKEN] == FIXTURE_USER_INPUT_TOKEN[CONF_TOKEN]
    assert result["data"][CONF_PLANT_ID] == "789012"
    assert result["data"][CONF_AUTH_TYPE] == AUTH_API_TOKEN
    assert result["data"][CONF_NAME] == "Test Plant 2"
    assert result["result"].unique_id == "789012"