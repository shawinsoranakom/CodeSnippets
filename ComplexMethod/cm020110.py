async def test_tunneling_setup_tcp_endpoint_select_skip(
    hass: HomeAssistant, knx_setup
) -> None:
    """Test tunneling TCP endpoint selection skipped if no slot info found."""
    gateway_udp = _gateway_descriptor("192.168.0.1", 3675)
    gateway_tcp_no_slots = _gateway_descriptor("192.168.1.100", 3675, True, slots=False)
    with patch(
        "homeassistant.components.knx.config_flow.GatewayScanner"
    ) as gateway_scanner_mock:
        gateway_scanner_mock.return_value = GatewayScannerMock(
            [gateway_udp, gateway_tcp_no_slots]
        )
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] is FlowResultType.FORM
        assert not result["errors"]

    tunnel_flow = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_KNX_CONNECTION_TYPE: CONF_KNX_TUNNELING,
        },
    )
    assert tunnel_flow["type"] is FlowResultType.FORM
    assert tunnel_flow["step_id"] == "tunnel"
    assert not tunnel_flow["errors"]

    result = await hass.config_entries.flow.async_configure(
        tunnel_flow["flow_id"],
        {CONF_KNX_GATEWAY: str(gateway_tcp_no_slots)},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        **DEFAULT_ENTRY_DATA,
        CONF_KNX_CONNECTION_TYPE: CONF_KNX_TUNNELING_TCP,
        CONF_HOST: "192.168.1.100",
        CONF_PORT: 3675,
        CONF_KNX_INDIVIDUAL_ADDRESS: "0.0.240",
        CONF_KNX_ROUTE_BACK: False,
        CONF_KNX_TUNNEL_ENDPOINT_IA: None,
        CONF_KNX_SECURE_DEVICE_AUTHENTICATION: None,
        CONF_KNX_SECURE_USER_ID: None,
        CONF_KNX_SECURE_USER_PASSWORD: None,
    }
    knx_setup.assert_called_once()