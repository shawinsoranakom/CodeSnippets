async def test_reconfigure_not_the_same_device(
    hass: HomeAssistant,
    mock_brother_client: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test starting the reconfiguration process, but with a different printer."""
    await init_integration(hass, mock_config_entry)

    result = await mock_config_entry.start_reconfigure_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    mock_brother_client.serial = "9876543210"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: "10.10.10.10",
            SECTION_ADVANCED_SETTINGS: {CONF_PORT: 161, CONF_COMMUNITY: "public"},
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"
    assert result["errors"] == {"base": "another_device"}

    mock_brother_client.serial = "0123456789"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: "11.11.11.11",
            SECTION_ADVANCED_SETTINGS: {CONF_PORT: 161, CONF_COMMUNITY: "public"},
        },
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert mock_config_entry.data == {
        CONF_HOST: "11.11.11.11",
        CONF_TYPE: "laser",
        SECTION_ADVANCED_SETTINGS: {CONF_PORT: 161, CONF_COMMUNITY: "public"},
    }