async def test_reconfigure(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_setup_entry: AsyncMock,
    mock_envoy: AsyncMock,
) -> None:
    """Test we can reconfiger the entry."""
    await setup_integration(hass, config_entry)
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
            CONF_USERNAME: "test-username2",
            CONF_PASSWORD: "test-password2",
        },
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"

    # changed entry
    assert config_entry.data[CONF_HOST] == "1.1.1.2"
    assert config_entry.data[CONF_USERNAME] == "test-username2"
    assert config_entry.data[CONF_PASSWORD] == "test-password2"