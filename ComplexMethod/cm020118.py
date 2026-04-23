async def test_reconfigure_flow_routing(hass: HomeAssistant, knx_setup) -> None:
    """Test reconfigure flow changing routing settings."""
    mock_config_entry = MockConfigEntry(
        title="KNX",
        domain="knx",
        data={
            **DEFAULT_ENTRY_DATA,
            CONF_KNX_CONNECTION_TYPE: CONF_KNX_ROUTING,
        },
    )
    gateway = _gateway_descriptor("192.168.0.1", 3676)
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
                CONF_KNX_CONNECTION_TYPE: CONF_KNX_ROUTING,
            },
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "routing"
        assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_KNX_INDIVIDUAL_ADDRESS: "2.0.4",
        },
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert mock_config_entry.data == {
        **DEFAULT_ENTRY_DATA,
        CONF_KNX_CONNECTION_TYPE: CONF_KNX_ROUTING,
        CONF_KNX_MCAST_GRP: DEFAULT_MCAST_GRP,
        CONF_KNX_MCAST_PORT: DEFAULT_MCAST_PORT,
        CONF_KNX_LOCAL_IP: None,
        CONF_KNX_INDIVIDUAL_ADDRESS: "2.0.4",
        CONF_KNX_SECURE_DEVICE_AUTHENTICATION: None,
        CONF_KNX_SECURE_USER_ID: None,
        CONF_KNX_SECURE_USER_PASSWORD: None,
        CONF_KNX_TUNNEL_ENDPOINT_IA: None,
    }
    knx_setup.assert_called_once()