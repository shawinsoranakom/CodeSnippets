async def test_reauth_flow_friendly_name_error(
    hass: HomeAssistant,
    exception: Exception,
    reason: str,
    config_entry: MockConfigEntry,
) -> None:
    """Test reauth flow with failures."""
    config_entry.add_to_hass(hass)
    assert config_entry.data[CONF_PIN] == "1234"

    result = await config_entry.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "device_config"

    with patch(
        "homeassistant.components.frontier_silicon.config_flow.AFSAPI.get_friendly_name",
        side_effect=exception,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_PIN: "4321"},
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "device_config"
    assert result2["errors"] == {"base": reason}

    result3 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_PIN: "4242"},
    )
    assert result3["type"] is FlowResultType.ABORT
    assert result3["reason"] == "reauth_successful"
    assert config_entry.data[CONF_PIN] == "4242"