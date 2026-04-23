async def test_routing_secure_manual_setup(
    gateway_scanner_mock, hass: HomeAssistant, knx_setup
) -> None:
    """Test routing secure setup with manual key config."""
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
            CONF_KNX_MCAST_PORT: 3671,
            CONF_KNX_INDIVIDUAL_ADDRESS: "0.0.123",
            CONF_KNX_ROUTING_SECURE: True,
        },
    )
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "secure_key_source_menu_routing"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"next_step_id": "secure_routing_manual"},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "secure_routing_manual"
    assert not result["errors"]

    result_invalid_key1 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_KNX_ROUTING_BACKBONE_KEY: "xxaacc44bbaacc44bbaacc44bbaaccyy",  # invalid hex string
            CONF_KNX_ROUTING_SYNC_LATENCY_TOLERANCE: 2000,
        },
    )
    assert result_invalid_key1["type"] is FlowResultType.FORM
    assert result_invalid_key1["step_id"] == "secure_routing_manual"
    assert result_invalid_key1["errors"] == {"backbone_key": "invalid_backbone_key"}

    result_invalid_key2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_KNX_ROUTING_BACKBONE_KEY: "bbaacc44bbaacc44",  # invalid length
            CONF_KNX_ROUTING_SYNC_LATENCY_TOLERANCE: 2000,
        },
    )
    assert result_invalid_key2["type"] is FlowResultType.FORM
    assert result_invalid_key2["step_id"] == "secure_routing_manual"
    assert result_invalid_key2["errors"] == {"backbone_key": "invalid_backbone_key"}

    secure_routing_manual = await hass.config_entries.flow.async_configure(
        result_invalid_key2["flow_id"],
        {
            CONF_KNX_ROUTING_BACKBONE_KEY: "bbaacc44bbaacc44bbaacc44bbaacc44",
            CONF_KNX_ROUTING_SYNC_LATENCY_TOLERANCE: 2000,
        },
    )
    assert secure_routing_manual["type"] is FlowResultType.CREATE_ENTRY
    assert secure_routing_manual["title"] == "Secure Routing as 0.0.123"
    assert secure_routing_manual["data"] == {
        **DEFAULT_ENTRY_DATA,
        CONF_KNX_CONNECTION_TYPE: CONF_KNX_ROUTING_SECURE,
        CONF_KNX_ROUTING_BACKBONE_KEY: "bbaacc44bbaacc44bbaacc44bbaacc44",
        CONF_KNX_ROUTING_SYNC_LATENCY_TOLERANCE: 2000,
        CONF_KNX_INDIVIDUAL_ADDRESS: "0.0.123",
        CONF_KNX_SECURE_DEVICE_AUTHENTICATION: None,
        CONF_KNX_SECURE_USER_ID: None,
        CONF_KNX_SECURE_USER_PASSWORD: None,
        CONF_KNX_TUNNEL_ENDPOINT_IA: None,
    }
    knx_setup.assert_called_once()