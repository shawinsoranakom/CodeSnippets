async def _get_menu_step_secure_tunnel(
    hass: HomeAssistant,
) -> config_entries.ConfigFlowResult:
    """Return flow in secure_tunnel menu step."""
    gateway = _gateway_descriptor(
        "192.168.0.1",
        3675,
        supports_tunnelling_tcp=True,
        requires_secure=True,
    )
    with patch(
        "homeassistant.components.knx.config_flow.GatewayScanner"
    ) as gateway_scanner_mock:
        gateway_scanner_mock.return_value = GatewayScannerMock([gateway])
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] is FlowResultType.FORM
        assert not result["errors"]

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
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
    return result