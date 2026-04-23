async def test_reconfigure_flow_secure_manual_to_keyfile(
    hass: HomeAssistant, knx_setup
) -> None:
    """Test reconfigure flow changing secure credential source."""
    mock_config_entry = MockConfigEntry(
        title="KNX",
        domain="knx",
        data={
            **DEFAULT_ENTRY_DATA,
            CONF_KNX_CONNECTION_TYPE: CONF_KNX_TUNNELING_TCP_SECURE,
            CONF_KNX_SECURE_USER_ID: 2,
            CONF_KNX_SECURE_USER_PASSWORD: "password",
            CONF_KNX_SECURE_DEVICE_AUTHENTICATION: "device_auth",
            CONF_KNX_KNXKEY_FILENAME: "knx/testcase.knxkeys",
            CONF_KNX_KNXKEY_PASSWORD: "invalid_password",
            CONF_HOST: "192.168.0.1",
            CONF_PORT: 3675,
            CONF_KNX_INDIVIDUAL_ADDRESS: "0.0.240",
            CONF_KNX_ROUTE_BACK: False,
            CONF_KNX_LOCAL_IP: None,
        },
    )
    gateway = _gateway_descriptor(
        "192.168.0.1",
        3675,
        supports_tunnelling_tcp=True,
        requires_secure=True,
    )

    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    knx_setup.reset_mock()
    menu_step = await mock_config_entry.start_reconfigure_flow(hass)
    with patch(
        "homeassistant.components.knx.config_flow.GatewayScanner"
    ) as gateway_scanner_mock:
        gateway_scanner_mock.return_value = GatewayScannerMock([gateway])
        result = await hass.config_entries.flow.async_configure(
            menu_step["flow_id"],
            {"next_step_id": "connection_type"},
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "connection_type"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_KNX_CONNECTION_TYPE: CONF_KNX_TUNNELING,
            },
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "tunnel"
        assert not result["errors"]

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_KNX_GATEWAY: str(gateway)},
    )
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "secure_key_source_menu_tunnel"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
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
        {CONF_KNX_TUNNEL_ENDPOINT_IA: "1.0.1"},
    )

    assert secure_knxkeys["type"] is FlowResultType.ABORT
    assert secure_knxkeys["reason"] == "reconfigure_successful"
    assert mock_config_entry.data == {
        **DEFAULT_ENTRY_DATA,
        CONF_KNX_CONNECTION_TYPE: CONF_KNX_TUNNELING_TCP_SECURE,
        CONF_KNX_KNXKEY_FILENAME: "knx/keyring.knxkeys",
        CONF_KNX_KNXKEY_PASSWORD: "test",
        CONF_KNX_SECURE_DEVICE_AUTHENTICATION: None,
        CONF_KNX_SECURE_USER_ID: None,
        CONF_KNX_SECURE_USER_PASSWORD: None,
        CONF_KNX_TUNNEL_ENDPOINT_IA: "1.0.1",
        CONF_KNX_ROUTING_BACKBONE_KEY: None,
        CONF_KNX_ROUTING_SYNC_LATENCY_TOLERANCE: None,
        CONF_HOST: "192.168.0.1",
        CONF_PORT: 3675,
        CONF_KNX_INDIVIDUAL_ADDRESS: "0.0.240",
        CONF_KNX_ROUTE_BACK: False,
        CONF_KNX_LOCAL_IP: None,
    }
    knx_setup.assert_called_once()