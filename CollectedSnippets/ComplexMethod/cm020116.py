async def test_reconfigure_flow_connection_type(
    hass: HomeAssistant, knx, mock_config_entry: MockConfigEntry
) -> None:
    """Test reconfigure flow changing interface."""
    # run one flow test with a set up integration (knx fixture)
    # instead of mocking async_setup_entry (knx_setup fixture) to test
    # usage of the already running XKNX instance for gateway scanner
    gateway = _gateway_descriptor("192.168.0.1", 3675)

    await knx.setup_integration()
    menu_step = await knx.mock_config_entry.start_reconfigure_flow(hass)

    with patch(
        "homeassistant.components.knx.config_flow.GatewayScanner"
    ) as gateway_scanner_mock:
        gateway_scanner_mock.return_value = GatewayScannerMock([gateway])
        result = await hass.config_entries.flow.async_configure(
            menu_step["flow_id"],
            {"next_step_id": "connection_type"},
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "connection_type"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_KNX_CONNECTION_TYPE: CONF_KNX_TUNNELING,
            },
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "tunnel"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_KNX_GATEWAY: str(gateway),
            },
        )
        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "reconfigure_successful"
        assert mock_config_entry.data == {
            CONF_KNX_CONNECTION_TYPE: CONF_KNX_TUNNELING,
            CONF_KNX_INDIVIDUAL_ADDRESS: "0.0.240",
            CONF_HOST: "192.168.0.1",
            CONF_PORT: 3675,
            CONF_KNX_MCAST_PORT: DEFAULT_MCAST_PORT,
            CONF_KNX_MCAST_GRP: DEFAULT_MCAST_GRP,
            CONF_KNX_RATE_LIMIT: 0,
            CONF_KNX_STATE_UPDATER: CONF_KNX_DEFAULT_STATE_UPDATER,
            CONF_KNX_ROUTE_BACK: False,
            CONF_KNX_TUNNEL_ENDPOINT_IA: None,
            CONF_KNX_SECURE_DEVICE_AUTHENTICATION: None,
            CONF_KNX_SECURE_USER_ID: None,
            CONF_KNX_SECURE_USER_PASSWORD: None,
        }