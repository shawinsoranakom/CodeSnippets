async def test_reauth(hass: HomeAssistant) -> None:
    """Test a reauth flow."""
    config_entry = MockConfigEntry(
        domain=const.DOMAIN,
        unique_id=TEST_GATEWAY_ID,
        data={
            const.CONF_CLOUD_USERNAME: None,
            const.CONF_CLOUD_PASSWORD: None,
            const.CONF_CLOUD_COUNTRY: None,
            const.CONF_FLOW_TYPE: const.CONF_GATEWAY,
            CONF_HOST: TEST_HOST,
            CONF_TOKEN: TEST_TOKEN,
            CONF_MODEL: TEST_MODEL,
            CONF_MAC: TEST_MAC,
        },
        title=TEST_NAME,
    )
    config_entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    result = await config_entry.start_reauth_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "cloud"
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            const.CONF_CLOUD_USERNAME: TEST_CLOUD_USER,
            const.CONF_CLOUD_PASSWORD: TEST_CLOUD_PASS,
            const.CONF_CLOUD_COUNTRY: TEST_CLOUD_COUNTRY,
        },
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"

    config_data = config_entry.data.copy()
    assert config_data == {
        const.CONF_FLOW_TYPE: const.CONF_GATEWAY,
        const.CONF_CLOUD_USERNAME: TEST_CLOUD_USER,
        const.CONF_CLOUD_PASSWORD: TEST_CLOUD_PASS,
        const.CONF_CLOUD_COUNTRY: TEST_CLOUD_COUNTRY,
        CONF_HOST: TEST_HOST,
        CONF_TOKEN: TEST_TOKEN,
        CONF_MODEL: TEST_MODEL,
        CONF_MAC: TEST_MAC,
    }