async def test_routing_secure_keyfile(
    gateway_scanner_mock, hass: HomeAssistant, knx_setup
) -> None:
    """Test routing secure setup with keyfile."""
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
        {"next_step_id": "secure_knxkeys"},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "secure_knxkeys"
    assert not result["errors"]

    with patch_file_upload():
        routing_secure_knxkeys = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_KEYRING_FILE: FIXTURE_UPLOAD_UUID,
                CONF_KNX_KNXKEY_PASSWORD: "password",
            },
        )
    assert routing_secure_knxkeys["type"] is FlowResultType.CREATE_ENTRY
    assert routing_secure_knxkeys["title"] == "Secure Routing as 0.0.123"
    assert routing_secure_knxkeys["data"] == {
        **DEFAULT_ENTRY_DATA,
        CONF_KNX_CONNECTION_TYPE: CONF_KNX_ROUTING_SECURE,
        CONF_KNX_KNXKEY_FILENAME: "knx/keyring.knxkeys",
        CONF_KNX_KNXKEY_PASSWORD: "password",
        CONF_KNX_ROUTING_BACKBONE_KEY: None,
        CONF_KNX_ROUTING_SYNC_LATENCY_TOLERANCE: None,
        CONF_KNX_SECURE_DEVICE_AUTHENTICATION: None,
        CONF_KNX_SECURE_USER_ID: None,
        CONF_KNX_SECURE_USER_PASSWORD: None,
        CONF_KNX_TUNNEL_ENDPOINT_IA: None,
        CONF_KNX_INDIVIDUAL_ADDRESS: "0.0.123",
    }
    knx_setup.assert_called_once()