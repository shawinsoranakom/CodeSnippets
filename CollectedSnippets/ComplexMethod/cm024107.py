async def test_reconfiguration_flow_update_configuration(
    hass: HomeAssistant,
    config_entry_setup: MockConfigEntry,
    mock_requests: Callable[[str], None],
) -> None:
    """Test that config flow reconfiguration updates configured device."""
    assert config_entry_setup.data[CONF_HOST] == "1.2.3.4"
    assert config_entry_setup.data[CONF_USERNAME] == "root"
    assert config_entry_setup.data[CONF_PASSWORD] == "pass"

    result = await config_entry_setup.start_reconfigure_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    mock_requests("2.3.4.5")
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: "2.3.4.5",
            CONF_USERNAME: "user",
        },
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert config_entry_setup.data[CONF_PROTOCOL] == "http"
    assert config_entry_setup.data[CONF_HOST] == "2.3.4.5"
    assert config_entry_setup.data[CONF_PORT] == 80
    assert config_entry_setup.data[CONF_USERNAME] == "user"
    assert config_entry_setup.data[CONF_PASSWORD] == "pass"