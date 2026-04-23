async def test_reauthentication_failure(
    hass: HomeAssistant,
) -> None:
    """Test UptimeRobot reauthentication failure."""
    old_entry = MockConfigEntry(**MOCK_UPTIMEROBOT_CONFIG_ENTRY_DATA)
    old_entry.add_to_hass(hass)

    result = await old_entry.start_reauth_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] is None
    assert result["step_id"] == "reauth_confirm"

    with (
        patch(
            "homeassistant.components.uptimerobot.config_flow.UptimeRobot.async_get_account_details",
            side_effect=UptimeRobotException,
        ),
        patch(
            "homeassistant.components.uptimerobot.async_setup_entry",
            return_value=True,
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_API_KEY: MOCK_UPTIMEROBOT_API_KEY},
        )
        await hass.async_block_till_done()

    assert result2["step_id"] == "reauth_confirm"
    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"]
    assert result2["errors"]["base"] == "cannot_connect"