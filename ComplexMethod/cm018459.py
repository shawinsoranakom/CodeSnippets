async def test_successful_reconfigure(
    hass: HomeAssistant,
    mock_airos_client: AsyncMock,
    mock_async_get_firmware_data: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test successful reconfigure."""
    mock_config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_config_entry.entry_id)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_RECONFIGURE, "entry_id": mock_config_entry.entry_id},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == RECONFIGURE_STEP

    user_input = {
        CONF_PASSWORD: NEW_PASSWORD,
        SECTION_ADVANCED_SETTINGS: {
            CONF_SSL: True,
            CONF_VERIFY_SSL: True,
        },
    }

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=user_input,
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"

    updated_entry = hass.config_entries.async_get_entry(mock_config_entry.entry_id)
    assert updated_entry.data[CONF_PASSWORD] == NEW_PASSWORD
    assert updated_entry.data[SECTION_ADVANCED_SETTINGS][CONF_SSL] is True
    assert updated_entry.data[SECTION_ADVANCED_SETTINGS][CONF_VERIFY_SSL] is True

    assert updated_entry.data[CONF_HOST] == MOCK_CONFIG[CONF_HOST]
    assert updated_entry.data[CONF_USERNAME] == MOCK_CONFIG[CONF_USERNAME]