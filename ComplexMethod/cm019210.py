async def test_reconfig(hass: HomeAssistant, mock_setup_entry: MagicMock) -> None:
    """Test a reconfiguration flow."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=format_mac(TEST_MAC),
        data={
            CONF_HOST: TEST_HOST,
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: TEST_PASSWORD,
            CONF_PORT: TEST_PORT,
            CONF_USE_HTTPS: TEST_USE_HTTPS,
            CONF_BC_PORT: TEST_BC_PORT,
            CONF_BC_ONLY: False,
        },
        options={
            CONF_PROTOCOL: DEFAULT_PROTOCOL,
        },
        title=TEST_NVR_NAME,
    )
    config_entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    result = await config_entry.start_reconfigure_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: TEST_HOST2,
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: TEST_PASSWORD,
        },
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert config_entry.data[CONF_HOST] == TEST_HOST2
    assert config_entry.data[CONF_USERNAME] == TEST_USERNAME
    assert config_entry.data[CONF_PASSWORD] == TEST_PASSWORD