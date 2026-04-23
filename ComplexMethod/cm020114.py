async def test_get_secure_menu_step_manual_tunnelling(
    request_description_mock: MagicMock,
    hass: HomeAssistant,
) -> None:
    """Test flow reaches secure_tunnellinn menu step from manual tunneling configuration."""
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

    manual_tunnel_flow = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_KNX_GATEWAY: OPTION_MANUAL_TUNNEL,
        },
    )

    result = await hass.config_entries.flow.async_configure(
        manual_tunnel_flow["flow_id"],
        {
            CONF_KNX_TUNNELING_TYPE: CONF_KNX_TUNNELING_TCP_SECURE,
            CONF_HOST: "192.168.0.1",
            CONF_PORT: 3675,
        },
    )
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "secure_key_source_menu_tunnel"