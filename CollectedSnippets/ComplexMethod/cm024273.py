async def test_try_connection_with_advanced_parameters(
    hass: HomeAssistant,
    mock_try_connection_success: MqttMockPahoClient,
    mock_context_client_key: bytes,
) -> None:
    """Test config flow with advanced parameters from config."""
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
            CONF_USERNAME: "user",
            CONF_PASSWORD: "pass",
            mqtt.CONF_TRANSPORT: "websockets",
            mqtt.CONF_CERTIFICATE: "auto",
            mqtt.CONF_TLS_INSECURE: True,
            mqtt.CONF_CLIENT_CERT: MOCK_CLIENT_CERT.decode(encoding="utf-8)"),
            mqtt.CONF_CLIENT_KEY: mock_context_client_key.decode(encoding="utf-8"),
            mqtt.CONF_WS_PATH: "/path/",
            mqtt.CONF_WS_HEADERS: {"h1": "v1", "h2": "v2"},
            mqtt.CONF_KEEPALIVE: 30,
            mqtt.CONF_DISCOVERY: True,
            mqtt.CONF_BIRTH_MESSAGE: {
                mqtt.ATTR_TOPIC: "ha_state/online",
                mqtt.ATTR_PAYLOAD: "online",
                mqtt.ATTR_QOS: 1,
                mqtt.ATTR_RETAIN: True,
            },
            mqtt.CONF_WILL_MESSAGE: {
                mqtt.ATTR_TOPIC: "ha_state/offline",
                mqtt.ATTR_PAYLOAD: "offline",
                mqtt.ATTR_QOS: 2,
                mqtt.ATTR_RETAIN: False,
            },
        },
    )

    # Test default/suggested values from config
    result = await config_entry.start_reconfigure_flow(hass, show_advanced_options=True)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "broker"
    defaults = {
        mqtt.CONF_BROKER: "test-broker",
        CONF_PORT: 1234,
        "set_client_cert": True,
        "set_ca_cert": "auto",
    }
    suggested = {
        CONF_USERNAME: "user",
        CONF_PASSWORD: PWD_NOT_CHANGED,
        mqtt.CONF_TLS_INSECURE: True,
        CONF_PROTOCOL: "3.1.1",
        mqtt.CONF_TRANSPORT: "websockets",
        mqtt.CONF_WS_PATH: "/path/",
        mqtt.CONF_WS_HEADERS: '{"h1":"v1","h2":"v2"}',
    }
    for k, v in defaults.items():
        assert get_default(result["data_schema"].schema, k) == v
    for k, v in suggested.items():
        assert get_schema_suggested_value(result["data_schema"].schema, k) == v

    # test we can change username and password
    mock_try_connection_success.reset_mock()
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            mqtt.CONF_BROKER: "another-broker",
            CONF_PORT: 2345,
            CONF_USERNAME: "us3r",
            CONF_PASSWORD: "p4ss",
            "set_ca_cert": "auto",
            "set_client_cert": True,
            mqtt.CONF_TLS_INSECURE: True,
            mqtt.CONF_TRANSPORT: "websockets",
            mqtt.CONF_WS_PATH: "/new/path",
            mqtt.CONF_WS_HEADERS: '{"h3": "v3"}',
        },
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    await hass.async_block_till_done()

    # check if the username and password was set from config flow and not from configuration.yaml
    assert mock_try_connection_success.username_pw_set.mock_calls[0][1] == (
        "us3r",
        "p4ss",
    )
    # check if tls_insecure_set is called
    assert mock_try_connection_success.tls_insecure_set.mock_calls[0][1] == (True,)

    def read_file(path: Path) -> bytes:
        with open(path, mode="rb") as file:
            return file.read()

    # check if the client certificate settings saved
    client_cert_path = await hass.async_add_executor_job(
        mqtt.util.get_file_path, mqtt.CONF_CLIENT_CERT
    )
    assert (
        mock_try_connection_success.tls_set.mock_calls[0].kwargs["certfile"]
        == client_cert_path
    )
    assert (
        await hass.async_add_executor_job(read_file, client_cert_path)
        == MOCK_CLIENT_CERT
    )

    client_key_path = await hass.async_add_executor_job(
        mqtt.util.get_file_path, mqtt.CONF_CLIENT_KEY
    )
    assert (
        mock_try_connection_success.tls_set.mock_calls[0].kwargs["keyfile"]
        == client_key_path
    )
    assert (
        await hass.async_add_executor_job(read_file, client_key_path)
        == mock_context_client_key
    )

    # check if websockets options are set
    assert mock_try_connection_success.ws_set_options.mock_calls[0][1] == (
        "/new/path",
        {"h3": "v3"},
    )
    await hass.async_block_till_done()