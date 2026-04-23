async def test_manual_tunnel_step_with_found_gateway(
    hass: HomeAssistant, gateway
) -> None:
    """Test manual tunnel if gateway was found and tunneling is selected."""
    with patch(
        "homeassistant.components.knx.config_flow.GatewayScanner"
    ) as gateway_scanner_mock:
        gateway_scanner_mock.return_value = GatewayScannerMock([gateway])
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

    manual_tunnel_flow = await hass.config_entries.flow.async_configure(
        tunnel_flow["flow_id"],
        {
            CONF_KNX_GATEWAY: OPTION_MANUAL_TUNNEL,
        },
    )
    assert manual_tunnel_flow["type"] is FlowResultType.FORM
    assert manual_tunnel_flow["step_id"] == "manual_tunnel"
    assert not manual_tunnel_flow["errors"]