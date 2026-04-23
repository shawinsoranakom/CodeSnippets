async def test_routing_setup(
    gateway_scanner_mock, hass: HomeAssistant, knx_setup
) -> None:
    """Test routing setup."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert not result["errors"]

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_KNX_CONNECTION_TYPE: CONF_KNX_ROUTING,
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "routing"
    assert result["errors"] == {"base": "no_router_discovered"}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_KNX_MCAST_GRP: DEFAULT_MCAST_GRP,
            CONF_KNX_MCAST_PORT: 3675,
            CONF_KNX_INDIVIDUAL_ADDRESS: "1.1.110",
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Routing as 1.1.110"
    assert result["data"] == {
        **DEFAULT_ENTRY_DATA,
        CONF_KNX_CONNECTION_TYPE: CONF_KNX_ROUTING,
        CONF_KNX_MCAST_GRP: DEFAULT_MCAST_GRP,
        CONF_KNX_MCAST_PORT: 3675,
        CONF_KNX_LOCAL_IP: None,
        CONF_KNX_INDIVIDUAL_ADDRESS: "1.1.110",
        CONF_KNX_SECURE_DEVICE_AUTHENTICATION: None,
        CONF_KNX_SECURE_USER_ID: None,
        CONF_KNX_SECURE_USER_PASSWORD: None,
        CONF_KNX_TUNNEL_ENDPOINT_IA: None,
    }
    knx_setup.assert_called_once()