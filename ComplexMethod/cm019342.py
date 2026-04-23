async def test_reconfigure_change_ip_to_existing(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_setup_entry: AsyncMock,
    mock_envoy: AsyncMock,
) -> None:
    """Test reconfiguration to existing entry with same ip does not harm existing one."""
    await setup_integration(hass, config_entry)
    other_entry = MockConfigEntry(
        domain=DOMAIN,
        entry_id="65432155aaddb2007c5f6602e0c38e72",
        title="Envoy 654321",
        unique_id="654321",
        data={
            CONF_HOST: "1.1.1.2",
            CONF_NAME: "Envoy 654321",
            CONF_USERNAME: "other-username",
            CONF_PASSWORD: "other-password",
        },
    )
    other_entry.add_to_hass(hass)

    # original other entry
    assert other_entry.data[CONF_HOST] == "1.1.1.2"
    assert other_entry.data[CONF_USERNAME] == "other-username"
    assert other_entry.data[CONF_PASSWORD] == "other-password"

    result = await config_entry.start_reconfigure_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"
    assert result["errors"] == {}

    # original entry
    assert config_entry.data[CONF_HOST] == "1.1.1.1"
    assert config_entry.data[CONF_USERNAME] == "test-username"
    assert config_entry.data[CONF_PASSWORD] == "test-password"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "1.1.1.2",
            CONF_USERNAME: "test-username",
            CONF_PASSWORD: "test-password2",
        },
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"

    # updated entry
    assert config_entry.data[CONF_HOST] == "1.1.1.2"
    assert config_entry.data[CONF_USERNAME] == "test-username"
    assert config_entry.data[CONF_PASSWORD] == "test-password2"

    # unchanged other entry
    assert other_entry.data[CONF_HOST] == "1.1.1.2"
    assert other_entry.data[CONF_USERNAME] == "other-username"
    assert other_entry.data[CONF_PASSWORD] == "other-password"