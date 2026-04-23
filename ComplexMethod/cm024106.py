async def test_reauth_flow_update_configuration(
    hass: HomeAssistant,
    config_entry_setup: MockConfigEntry,
    mock_requests: Callable[[str], None],
) -> None:
    """Test that config flow fails on already configured device."""
    assert config_entry_setup.data[CONF_HOST] == "1.2.3.4"
    assert config_entry_setup.data[CONF_USERNAME] == "root"
    assert config_entry_setup.data[CONF_PASSWORD] == "pass"

    result = await config_entry_setup.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    mock_requests("2.3.4.5")
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_PROTOCOL: "https",
            CONF_HOST: "2.3.4.5",
            CONF_USERNAME: "user2",
            CONF_PASSWORD: "pass2",
            CONF_PORT: 443,
        },
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert config_entry_setup.data[CONF_PROTOCOL] == "https"
    assert config_entry_setup.data[CONF_HOST] == "2.3.4.5"
    assert config_entry_setup.data[CONF_PORT] == 443
    assert config_entry_setup.data[CONF_USERNAME] == "user2"
    assert config_entry_setup.data[CONF_PASSWORD] == "pass2"