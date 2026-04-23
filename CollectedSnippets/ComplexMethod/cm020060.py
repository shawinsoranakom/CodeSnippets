async def test_options_flow(hass: HomeAssistant) -> None:
    """Test options flow."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=TEST_CLOUD_DATA["username"],
        data=TEST_CLOUD_DATA,
    )

    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input=TEST_OPTIONS,
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "risco_to_ha"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input=TEST_RISCO_TO_HA,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "ha_to_risco"

    with patch("homeassistant.components.risco.async_setup_entry", return_value=True):
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input=TEST_HA_TO_RISCO,
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options == {
        **TEST_OPTIONS,
        "risco_states_to_ha": TEST_RISCO_TO_HA,
        "ha_states_to_risco": TEST_HA_TO_RISCO,
    }