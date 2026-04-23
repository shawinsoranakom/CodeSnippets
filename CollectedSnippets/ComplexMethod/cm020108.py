async def test_tunneling_setup_for_local_ip(
    request_description_mock: MagicMock,
    gateway_scanner_mock: MagicMock,
    hass: HomeAssistant,
    knx_setup,
) -> None:
    """Test tunneling if only one gateway is found."""
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
            CONF_KNX_CONNECTION_TYPE: CONF_KNX_TUNNELING,
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "manual_tunnel"
    assert result["errors"] == {"base": "no_tunnel_discovered"}

    # invalid host ip address
    result_invalid_host = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_KNX_TUNNELING_TYPE: CONF_KNX_TUNNELING,
            CONF_HOST: DEFAULT_MCAST_GRP,  # multicast addresses are invalid
            CONF_PORT: 3675,
            CONF_KNX_LOCAL_IP: "192.168.1.112",
        },
    )
    assert result_invalid_host["type"] is FlowResultType.FORM
    assert result_invalid_host["step_id"] == "manual_tunnel"
    assert result_invalid_host["errors"] == {
        CONF_HOST: "invalid_ip_address",
        "base": "no_tunnel_discovered",
    }
    # invalid local ip address
    with patch(
        "homeassistant.components.knx.config_flow.xknx_validate_ip",
        new=AsyncMock(side_effect=_mock_validate_ip_for_invalid_local),
    ):
        result_invalid_local = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_KNX_TUNNELING_TYPE: CONF_KNX_TUNNELING,
                CONF_HOST: "192.168.0.2",
                CONF_PORT: 3675,
                CONF_KNX_LOCAL_IP: "asdf",
            },
        )
    assert result_invalid_local["type"] is FlowResultType.FORM
    assert result_invalid_local["step_id"] == "manual_tunnel"
    assert result_invalid_local["errors"] == {
        CONF_KNX_LOCAL_IP: "invalid_ip_address",
        "base": "no_tunnel_discovered",
    }

    # valid user input
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_KNX_TUNNELING_TYPE: CONF_KNX_TUNNELING,
            CONF_HOST: "192.168.0.2",
            CONF_PORT: 3675,
            CONF_KNX_LOCAL_IP: "192.168.1.112",
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Tunneling UDP @ 192.168.0.2"
    assert result["data"] == {
        **DEFAULT_ENTRY_DATA,
        CONF_KNX_CONNECTION_TYPE: CONF_KNX_TUNNELING,
        CONF_HOST: "192.168.0.2",
        CONF_PORT: 3675,
        CONF_KNX_INDIVIDUAL_ADDRESS: "0.0.240",
        CONF_KNX_ROUTE_BACK: False,
        CONF_KNX_LOCAL_IP: "192.168.1.112",
        CONF_KNX_TUNNEL_ENDPOINT_IA: None,
        CONF_KNX_SECURE_DEVICE_AUTHENTICATION: None,
        CONF_KNX_SECURE_USER_ID: None,
        CONF_KNX_SECURE_USER_PASSWORD: None,
    }
    knx_setup.assert_called_once()