async def test_reauth_flow_update_configuration(
    hass: HomeAssistant, config_entry_setup: MockConfigEntry
) -> None:
    """Verify reauth flow can update hub configuration."""
    config_entry = config_entry_setup

    result = await config_entry.start_reauth_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    with patch(
        "homeassistant.components.unifi.UnifiHub.available", new_callable=PropertyMock
    ) as ws_mock:
        ws_mock.return_value = False
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_HOST: "1.2.3.4",
                CONF_USERNAME: "new_name",
                CONF_PASSWORD: "new_pass",
                CONF_PORT: 1234,
                CONF_VERIFY_SSL: True,
            },
        )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert config_entry.data[CONF_HOST] == "1.2.3.4"
    assert config_entry.data[CONF_USERNAME] == "new_name"
    assert config_entry.data[CONF_PASSWORD] == "new_pass"