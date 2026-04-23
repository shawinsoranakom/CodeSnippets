async def test_change_connection_settings(hass: HomeAssistant) -> None:
    """Test changing connection settings by issuing a second user config flow."""
    config_entry = MockConfigEntry(
        domain=const.DOMAIN,
        unique_id=TEST_MAC,
        data={
            CONF_HOST: TEST_HOST,
            CONF_API_KEY: TEST_API_KEY,
            const.CONF_INTERFACE: TEST_HOST_HA,
        },
        title=DEFAULT_GATEWAY_NAME,
    )
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        const.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: TEST_HOST2},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "connect"
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_API_KEY: TEST_API_KEY2},
    )

    assert result["type"] is FlowResultType.ABORT
    assert config_entry.data[CONF_HOST] == TEST_HOST2
    assert config_entry.data[CONF_API_KEY] == TEST_API_KEY2
    assert config_entry.data[const.CONF_INTERFACE] == TEST_HOST_ANY