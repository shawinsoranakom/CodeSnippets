async def test_configure_secure_knxkeys(hass: HomeAssistant, knx_setup) -> None:
    """Test configure secure knxkeys."""
    menu_step = await _get_menu_step_secure_tunnel(hass)

    result = await hass.config_entries.flow.async_configure(
        menu_step["flow_id"],
        {"next_step_id": "secure_knxkeys"},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "secure_knxkeys"
    assert not result["errors"]

    with patch_file_upload():
        secure_knxkeys = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_KEYRING_FILE: FIXTURE_UPLOAD_UUID,
                CONF_KNX_KNXKEY_PASSWORD: "test",
            },
        )
    assert result["type"] is FlowResultType.FORM
    assert secure_knxkeys["step_id"] == "knxkeys_tunnel_select"
    assert not result["errors"]
    secure_knxkeys = await hass.config_entries.flow.async_configure(
        secure_knxkeys["flow_id"],
        {CONF_KNX_TUNNEL_ENDPOINT_IA: CONF_KNX_AUTOMATIC},
    )

    assert secure_knxkeys["type"] is FlowResultType.CREATE_ENTRY
    assert secure_knxkeys["data"] == {
        **DEFAULT_ENTRY_DATA,
        CONF_KNX_CONNECTION_TYPE: CONF_KNX_TUNNELING_TCP_SECURE,
        CONF_KNX_KNXKEY_FILENAME: "knx/keyring.knxkeys",
        CONF_KNX_KNXKEY_PASSWORD: "test",
        CONF_KNX_ROUTING_BACKBONE_KEY: None,
        CONF_KNX_ROUTING_SYNC_LATENCY_TOLERANCE: None,
        CONF_KNX_SECURE_DEVICE_AUTHENTICATION: None,
        CONF_KNX_SECURE_USER_ID: None,
        CONF_KNX_SECURE_USER_PASSWORD: None,
        CONF_KNX_TUNNEL_ENDPOINT_IA: None,
        CONF_HOST: "192.168.0.1",
        CONF_PORT: 3675,
        CONF_KNX_INDIVIDUAL_ADDRESS: "0.0.240",
        CONF_KNX_ROUTE_BACK: False,
        CONF_KNX_LOCAL_IP: None,
    }
    knx_setup.assert_called_once()