async def test_reconfigure_same_nvr_updated_credentials(
    hass: HomeAssistant,
    bootstrap: Bootstrap,
    nvr: NVR,
    mock_api_bootstrap: Mock,
    mock_api_meta_info: Mock,
    mock_setup: AsyncMock,
) -> None:
    """Test reconfiguration flow updating credentials for same NVR."""
    # Use the NVR's actual MAC address
    nvr_mac = _async_unifi_mac_from_hass(nvr.mac)

    mock_config = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_HOST: "1.1.1.1",
            CONF_USERNAME: "old-username",
            CONF_PASSWORD: "old-password",
            CONF_API_KEY: "old-api-key",
            "id": "UnifiProtect",
            CONF_PORT: 443,
            CONF_VERIFY_SSL: False,
        },
        unique_id=nvr_mac,
    )
    mock_config.add_to_hass(hass)

    result = await mock_config.start_reconfigure_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    bootstrap.nvr = nvr
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "2.2.2.2",
            CONF_PORT: 8443,
            CONF_VERIFY_SSL: True,
            CONF_USERNAME: "new-username",
            CONF_PASSWORD: "new-password",
            CONF_API_KEY: "new-api-key",
        },
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    # Verify unique_id remains the same
    assert mock_config.unique_id == nvr_mac
    # Verify credentials were updated
    assert mock_config.data[CONF_HOST] == "2.2.2.2"
    assert mock_config.data[CONF_PORT] == 8443
    assert mock_config.data[CONF_VERIFY_SSL] is True
    assert mock_config.data[CONF_USERNAME] == "new-username"
    assert mock_config.data[CONF_PASSWORD] == "new-password"
    assert mock_config.data[CONF_API_KEY] == "new-api-key"