async def test_setup_with_advanced_settings(
    hass: HomeAssistant,
    mock_try_connection: MagicMock,
    mock_process_uploaded_file: MagicMock,
) -> None:
    """Test config flow setup with advanced parameters."""
    file_id = mock_process_uploaded_file.file_id

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
        },
    )

    mock_try_connection.return_value = True

    result = await config_entry.start_reconfigure_flow(hass, show_advanced_options=True)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "broker"
    assert result["data_schema"].schema["advanced_options"]

    # first iteration, basic settings
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            mqtt.CONF_BROKER: "test-broker",
            CONF_PORT: 2345,
            CONF_USERNAME: "user",
            CONF_PASSWORD: "secret",
            "advanced_options": True,
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "broker"
    assert "advanced_options" not in result["data_schema"].schema
    assert result["data_schema"].schema[CONF_CLIENT_ID]
    assert result["data_schema"].schema[mqtt.CONF_KEEPALIVE]
    assert result["data_schema"].schema["set_client_cert"]
    assert result["data_schema"].schema["set_ca_cert"]
    assert result["data_schema"].schema[mqtt.CONF_TLS_INSECURE]
    assert result["data_schema"].schema[CONF_PROTOCOL]
    assert result["data_schema"].schema[mqtt.CONF_TRANSPORT]
    assert mqtt.CONF_CLIENT_CERT not in result["data_schema"].schema
    assert mqtt.CONF_CLIENT_KEY not in result["data_schema"].schema

    # second iteration, advanced settings with request for client cert
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            mqtt.CONF_BROKER: "test-broker",
            CONF_PORT: 2345,
            CONF_USERNAME: "user",
            CONF_PASSWORD: "secret",
            mqtt.CONF_KEEPALIVE: 30,
            "set_ca_cert": "auto",
            "set_client_cert": True,
            mqtt.CONF_TLS_INSECURE: True,
            CONF_PROTOCOL: "3.1.1",
            mqtt.CONF_TRANSPORT: "websockets",
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "broker"
    assert "advanced_options" not in result["data_schema"].schema
    assert result["data_schema"].schema[CONF_CLIENT_ID]
    assert result["data_schema"].schema[mqtt.CONF_KEEPALIVE]
    assert result["data_schema"].schema["set_client_cert"]
    assert result["data_schema"].schema["set_ca_cert"]
    assert result["data_schema"].schema[mqtt.CONF_TLS_INSECURE]
    assert result["data_schema"].schema[CONF_PROTOCOL]
    assert result["data_schema"].schema[mqtt.CONF_CLIENT_CERT]
    assert result["data_schema"].schema[mqtt.CONF_CLIENT_KEY]
    assert result["data_schema"].schema[mqtt.CONF_TRANSPORT]
    assert result["data_schema"].schema[mqtt.CONF_WS_PATH]
    assert result["data_schema"].schema[mqtt.CONF_WS_HEADERS]

    # third iteration, advanced settings with client cert and key set and bad json payload
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            mqtt.CONF_BROKER: "test-broker",
            CONF_PORT: 2345,
            CONF_USERNAME: "user",
            CONF_PASSWORD: "secret",
            mqtt.CONF_KEEPALIVE: 30,
            "set_ca_cert": "auto",
            "set_client_cert": True,
            mqtt.CONF_CLIENT_CERT: file_id[mqtt.CONF_CLIENT_CERT],
            mqtt.CONF_CLIENT_KEY: file_id[mqtt.CONF_CLIENT_KEY],
            mqtt.CONF_TLS_INSECURE: True,
            mqtt.CONF_TRANSPORT: "websockets",
            mqtt.CONF_WS_PATH: "/custom_path/",
            mqtt.CONF_WS_HEADERS: '{"header_1": "content_header_1", "header_2": "content_header_2"',
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "broker"
    assert result["errors"]["base"] == "bad_ws_headers"

    # fourth iteration, advanced settings with client cert and key set
    # and correct json payload for ws_headers
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            mqtt.CONF_BROKER: "test-broker",
            CONF_PORT: 2345,
            CONF_USERNAME: "user",
            CONF_PASSWORD: "secret",
            mqtt.CONF_KEEPALIVE: 30,
            "set_ca_cert": "auto",
            "set_client_cert": True,
            mqtt.CONF_CLIENT_CERT: file_id[mqtt.CONF_CLIENT_CERT],
            mqtt.CONF_CLIENT_KEY: file_id[mqtt.CONF_CLIENT_KEY],
            mqtt.CONF_TLS_INSECURE: True,
            mqtt.CONF_TRANSPORT: "websockets",
            mqtt.CONF_WS_PATH: "/custom_path/",
            mqtt.CONF_WS_HEADERS: '{"header_1": "content_header_1", "header_2": "content_header_2"}',
        },
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"

    # Check config entry result
    assert config_entry.data == {
        mqtt.CONF_BROKER: "test-broker",
        CONF_PORT: 2345,
        CONF_USERNAME: "user",
        CONF_PASSWORD: "secret",
        mqtt.CONF_KEEPALIVE: 30,
        mqtt.CONF_CLIENT_CERT: MOCK_CLIENT_CERT.decode(encoding="utf-8"),
        mqtt.CONF_CLIENT_KEY: MOCK_CLIENT_KEY.decode(encoding="utf-8"),
        "tls_insecure": True,
        mqtt.CONF_TRANSPORT: "websockets",
        mqtt.CONF_WS_PATH: "/custom_path/",
        mqtt.CONF_WS_HEADERS: {
            "header_1": "content_header_1",
            "header_2": "content_header_2",
        },
        mqtt.CONF_CERTIFICATE: "auto",
    }