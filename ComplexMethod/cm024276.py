async def test_change_websockets_transport_to_tcp(
    hass: HomeAssistant, mock_try_connection: MagicMock
) -> None:
    """Test reconfiguration flow changing websockets transport settings."""
    config_entry = MockConfigEntry(
        domain=mqtt.DOMAIN,
        version=mqtt.CONFIG_ENTRY_VERSION,
        minor_version=mqtt.CONFIG_ENTRY_MINOR_VERSION,
    )
    config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        config_entry,
        data={
            mqtt.CONF_BROKER: "test-broker",
            CONF_PORT: 1234,
            mqtt.CONF_TRANSPORT: "websockets",
            mqtt.CONF_WS_HEADERS: {"header_1": "custom_header1"},
            mqtt.CONF_WS_PATH: "/some_path",
        },
    )

    mock_try_connection.return_value = True

    result = await config_entry.start_reconfigure_flow(hass, show_advanced_options=True)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "broker"
    assert result["data_schema"].schema["transport"]
    assert result["data_schema"].schema["ws_path"]
    assert result["data_schema"].schema["ws_headers"]

    # Change transport to tcp
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            mqtt.CONF_BROKER: "test-broker",
            CONF_PORT: 1234,
            mqtt.CONF_TRANSPORT: "tcp",
            mqtt.CONF_WS_HEADERS: '{"header_1": "custom_header1"}',
            mqtt.CONF_WS_PATH: "/some_path",
        },
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"

    # Check config entry result
    assert config_entry.data == {
        mqtt.CONF_BROKER: "test-broker",
        CONF_PORT: 1234,
        mqtt.CONF_TRANSPORT: "tcp",
    }