async def test_tunneling_setup_manual_request_description_error(
    gateway_scanner_mock: MagicMock,
    hass: HomeAssistant,
    knx_setup,
) -> None:
    """Test tunneling if no gateway was found found (or `manual` option was chosen)."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_KNX_CONNECTION_TYPE: CONF_KNX_TUNNELING,
        },
    )
    assert result["step_id"] == "manual_tunnel"
    assert result["errors"] == {"base": "no_tunnel_discovered"}

    # TCP configured but not supported by gateway
    with patch(
        "homeassistant.components.knx.config_flow.request_description",
        return_value=_gateway_descriptor(
            "192.168.0.1",
            3671,
            supports_tunnelling_tcp=False,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_KNX_TUNNELING_TYPE: CONF_KNX_TUNNELING_TCP,
                CONF_HOST: "192.168.0.1",
                CONF_PORT: 3671,
            },
        )
        assert result["step_id"] == "manual_tunnel"
        assert result["errors"] == {
            "base": "no_tunnel_discovered",
            "tunneling_type": "unsupported_tunnel_type",
        }
    # TCP configured but Secure required by gateway
    with patch(
        "homeassistant.components.knx.config_flow.request_description",
        return_value=_gateway_descriptor(
            "192.168.0.1",
            3671,
            supports_tunnelling_tcp=True,
            requires_secure=True,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_KNX_TUNNELING_TYPE: CONF_KNX_TUNNELING_TCP,
                CONF_HOST: "192.168.0.1",
                CONF_PORT: 3671,
            },
        )
        assert result["step_id"] == "manual_tunnel"
        assert result["errors"] == {
            "base": "no_tunnel_discovered",
            "tunneling_type": "unsupported_tunnel_type",
        }
    # Secure configured but not enabled on gateway
    with patch(
        "homeassistant.components.knx.config_flow.request_description",
        return_value=_gateway_descriptor(
            "192.168.0.1",
            3671,
            supports_tunnelling_tcp=True,
            requires_secure=False,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_KNX_TUNNELING_TYPE: CONF_KNX_TUNNELING_TCP_SECURE,
                CONF_HOST: "192.168.0.1",
                CONF_PORT: 3671,
            },
        )
        assert result["step_id"] == "manual_tunnel"
        assert result["errors"] == {
            "base": "no_tunnel_discovered",
            "tunneling_type": "unsupported_tunnel_type",
        }
    # No connection to gateway
    with patch(
        "homeassistant.components.knx.config_flow.request_description",
        side_effect=CommunicationError(""),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_KNX_TUNNELING_TYPE: CONF_KNX_TUNNELING_TCP,
                CONF_HOST: "192.168.0.1",
                CONF_PORT: 3671,
            },
        )
        assert result["step_id"] == "manual_tunnel"
        assert result["errors"] == {"base": "cannot_connect"}
    # OK configuration
    with patch(
        "homeassistant.components.knx.config_flow.request_description",
        return_value=_gateway_descriptor(
            "192.168.0.1",
            3671,
            supports_tunnelling_tcp=True,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_KNX_TUNNELING_TYPE: CONF_KNX_TUNNELING_TCP,
                CONF_HOST: "192.168.0.1",
                CONF_PORT: 3671,
            },
        )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Tunneling TCP @ 192.168.0.1"
    assert result["data"] == {
        **DEFAULT_ENTRY_DATA,
        CONF_KNX_CONNECTION_TYPE: CONF_KNX_TUNNELING_TCP,
        CONF_HOST: "192.168.0.1",
        CONF_PORT: 3671,
        CONF_KNX_TUNNEL_ENDPOINT_IA: None,
        CONF_KNX_SECURE_DEVICE_AUTHENTICATION: None,
        CONF_KNX_SECURE_USER_ID: None,
        CONF_KNX_SECURE_USER_PASSWORD: None,
    }
    knx_setup.assert_called_once()