async def test_reauth(hass: HomeAssistant, mock_get_stations_401_error) -> None:
    """Test a reauth_flow."""

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_API_TOKEN: "same_same",
        },
    )
    entry.add_to_hass(hass)

    assert not await hass.config_entries.async_setup(entry.entry_id)
    assert entry.state is ConfigEntryState.SETUP_ERROR

    result = await entry.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_API_TOKEN: "SAME_SAME"}
    )

    assert result["reason"] == "reauth_successful"
    assert result["type"] is FlowResultType.ABORT
    assert entry.data[CONF_API_TOKEN] == "SAME_SAME"