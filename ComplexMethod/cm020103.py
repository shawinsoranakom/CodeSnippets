async def test_routing_setup_advanced(
    gateway_scanner_mock, hass: HomeAssistant, knx_setup
) -> None:
    """Test routing setup with advanced options."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_USER,
            "show_advanced_options": True,
        },
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

    # invalid user input
    with patch(
        "homeassistant.components.knx.config_flow.xknx_validate_ip",
        new=AsyncMock(side_effect=_mock_validate_ip_for_invalid_local),
    ):
        result_invalid_input = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_KNX_MCAST_GRP: "10.1.2.3",  # no valid multicast group
                CONF_KNX_MCAST_PORT: 3675,
                CONF_KNX_INDIVIDUAL_ADDRESS: "not_a_valid_address",
                CONF_KNX_LOCAL_IP: "no_local_ip",
            },
        )
    assert result_invalid_input["type"] is FlowResultType.FORM
    assert result_invalid_input["step_id"] == "routing"
    assert result_invalid_input["errors"] == {
        CONF_KNX_MCAST_GRP: "invalid_ip_address",
        CONF_KNX_INDIVIDUAL_ADDRESS: "invalid_individual_address",
        CONF_KNX_LOCAL_IP: "invalid_ip_address",
        "base": "no_router_discovered",
    }

    # valid user input
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_KNX_MCAST_GRP: DEFAULT_MCAST_GRP,
            CONF_KNX_MCAST_PORT: 3675,
            CONF_KNX_INDIVIDUAL_ADDRESS: "1.1.110",
            CONF_KNX_LOCAL_IP: "192.168.1.112",
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Routing as 1.1.110"
    assert result["data"] == {
        **DEFAULT_ENTRY_DATA,
        CONF_KNX_CONNECTION_TYPE: CONF_KNX_ROUTING,
        CONF_KNX_MCAST_GRP: DEFAULT_MCAST_GRP,
        CONF_KNX_MCAST_PORT: 3675,
        CONF_KNX_LOCAL_IP: "192.168.1.112",
        CONF_KNX_INDIVIDUAL_ADDRESS: "1.1.110",
        CONF_KNX_SECURE_DEVICE_AUTHENTICATION: None,
        CONF_KNX_SECURE_USER_ID: None,
        CONF_KNX_SECURE_USER_PASSWORD: None,
        CONF_KNX_TUNNEL_ENDPOINT_IA: None,
    }
    knx_setup.assert_called_once()