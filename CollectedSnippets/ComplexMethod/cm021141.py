async def test_reconfigure(
    hass: HomeAssistant,
    bootstrap: Bootstrap,
    nvr: NVR,
    ufp_reauth_entry: MockConfigEntry,
    mock_api_bootstrap: Mock,
    mock_api_meta_info: Mock,
    mock_setup: AsyncMock,
) -> None:
    """Test reconfiguration flow."""
    ufp_reauth_entry.add_to_hass(hass)

    result = await ufp_reauth_entry.start_reconfigure_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    # Test with connection error
    nvr.mac = _async_unifi_mac_from_hass(MAC_ADDR)
    bootstrap.nvr = nvr
    mock_api_bootstrap.side_effect = [NvrError, bootstrap]

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            **RECONFIGURE_USER_INPUT,
            CONF_HOST: "1.1.1.2",
            CONF_PASSWORD: "new-password",
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}

    # Test successful reconfiguration with matching NVR MAC
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            **RECONFIGURE_USER_INPUT,
            CONF_HOST: "1.1.1.2",
            CONF_PASSWORD: "new-password",
            CONF_API_KEY: "new-api-key",
        },
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert ufp_reauth_entry.data[CONF_HOST] == "1.1.1.2"
    assert ufp_reauth_entry.data[CONF_PASSWORD] == "new-password"
    assert ufp_reauth_entry.data[CONF_API_KEY] == "new-api-key"