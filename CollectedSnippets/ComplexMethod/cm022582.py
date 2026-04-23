async def test_reconfigure_failed(
    hass: HomeAssistant,
) -> None:
    """Test that the entry reconfigure fails with a wrong key."""
    config_entry = MockConfigEntry(
        **{**MOCK_UPTIMEROBOT_CONFIG_ENTRY_DATA, "unique_id": None}
    )
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reconfigure_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] is None
    assert result["step_id"] == "reconfigure"

    wrong_key = "u0242ac120003-wrong"

    with (
        patch(
            "homeassistant.components.uptimerobot.config_flow.UptimeRobot.async_get_account_details",
            side_effect=UptimeRobotAuthenticationException,
        ),
        patch(
            "homeassistant.components.uptimerobot.async_setup_entry",
            return_value=True,
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_API_KEY: wrong_key},
        )

    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"]
    assert result2["errors"]["base"] == "invalid_api_key"

    new_key = "u0242ac120003-new"

    with (
        patch(
            "homeassistant.components.uptimerobot.config_flow.UptimeRobot.async_get_account_details",
            return_value=mock_uptimerobot_api_response(
                api_path=API_PATH_USER_ME, data=MOCK_UPTIMEROBOT_ACCOUNT
            ),
        ),
        patch(
            "homeassistant.components.uptimerobot.async_setup_entry",
            return_value=True,
        ),
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            user_input={CONF_API_KEY: new_key},
        )

    assert result3["type"] is FlowResultType.ABORT
    assert result3["reason"] == "reconfigure_successful"

    # changed entry
    assert config_entry.data[CONF_API_KEY] == new_key