async def test_reconfigure_auth_failure(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_setup_entry: AsyncMock,
    mock_envoy: AsyncMock,
    exception: Exception,
    error: str,
) -> None:
    """Test changing credentials for existing host with auth failure."""
    await setup_integration(hass, config_entry)

    result = await config_entry.start_reconfigure_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    # existing config
    assert config_entry.data[CONF_HOST] == "1.1.1.1"
    assert config_entry.data[CONF_USERNAME] == "test-username"
    assert config_entry.data[CONF_PASSWORD] == "test-password"

    mock_envoy.authenticate.side_effect = exception

    # mock failing authentication on first try
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "1.1.1.2",
            CONF_USERNAME: "test-username",
            CONF_PASSWORD: "wrong-password",
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": error}

    mock_envoy.authenticate.side_effect = None
    # mock successful authentication and update of credentials
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "1.1.1.2",
            CONF_USERNAME: "test-username",
            CONF_PASSWORD: "changed-password",
        },
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"

    # updated config with new ip and changed pw
    assert config_entry.data[CONF_HOST] == "1.1.1.2"
    assert config_entry.data[CONF_USERNAME] == "test-username"
    assert config_entry.data[CONF_PASSWORD] == "changed-password"